"""Localisation d'infrastructures critiques via Overpass / OpenStreetMap.

Usage :
    python locate_infra.py <lat> <lon> [--radius 2000] [--types health,emergency,education,transport,roads,shelter,all]
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.openstreetmap.fr/api/interpreter",
]
TIMEOUT_S = 60

# Mapping catégorie -> liste de (clé, valeurs OSM)
CATEGORY_FILTERS: dict[str, list[tuple[str, list[str]]]] = {
    "health": [
        ("amenity", ["hospital", "clinic", "doctors", "pharmacy"]),
    ],
    "emergency": [
        ("amenity", ["fire_station", "police"]),
    ],
    "education": [
        ("amenity", ["school", "kindergarten", "college", "university"]),
    ],
    "transport": [
        ("amenity", ["bus_station"]),
        ("railway", ["station", "halt"]),
        ("aeroway", ["aerodrome"]),
    ],
    "roads": [
        ("highway", ["motorway", "trunk", "primary", "secondary"]),
    ],
    "shelter": [
        ("amenity", ["townhall", "community_centre"]),
        ("leisure", ["sports_centre"]),
        ("building", ["public"]),
    ],
}

ALL_CATEGORIES = list(CATEGORY_FILTERS.keys())


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance en mètres entre deux points GPS (formule de Haversine)."""
    r = 6_371_000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmbd = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmbd / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def build_overpass_query(lat: float, lon: float, radius: int, categories: list[str]) -> str:
    """Construit une requête Overpass QL pour les catégories demandées."""
    blocks: list[str] = []
    for cat in categories:
        for key, values in CATEGORY_FILTERS[cat]:
            values_re = "|".join(values)
            for elt in ("node", "way", "relation"):
                blocks.append(
                    f'  {elt}["{key}"~"^({values_re})$"](around:{radius},{lat},{lon});'
                )
    body = "\n".join(blocks)
    return f"[out:json][timeout:{TIMEOUT_S}];\n(\n{body}\n);\nout center tags;"


def overpass_query(query: str) -> dict:
    """Tente la requête sur chaque miroir Overpass, avec un retry sur les erreurs transitoires."""
    data = urllib.parse.urlencode({"data": query}).encode("utf-8")
    last_err: Exception | None = None
    for url in OVERPASS_URLS:
        for attempt in range(2):
            try:
                req = urllib.request.Request(
                    url, data=data, headers={"User-Agent": "plugin-urgence-fr/0.1"}
                )
                with urllib.request.urlopen(req, timeout=TIMEOUT_S + 10) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                last_err = e
                if e.code in (429, 502, 503, 504) and attempt == 0:
                    time.sleep(2)
                    continue
                break
            except (urllib.error.URLError, TimeoutError) as e:
                last_err = e
                break
    raise last_err if last_err else RuntimeError("Overpass: tous les miroirs ont échoué")


def categorize_element(tags: dict) -> tuple[str | None, str | None]:
    """Retourne (category, kind) à partir des tags OSM."""
    for cat, filters in CATEGORY_FILTERS.items():
        for key, values in filters:
            if tags.get(key) in values:
                return cat, tags.get(key)
    return None, None


def element_coords(element: dict) -> tuple[float | None, float | None]:
    if element.get("type") == "node":
        return element.get("lat"), element.get("lon")
    center = element.get("center", {})
    return center.get("lat"), center.get("lon")


def fetch_infrastructure(lat: float, lon: float, radius: int, categories: list[str]) -> dict:
    query = build_overpass_query(lat, lon, radius, categories)
    raw = overpass_query(query)

    results: dict[str, list[dict]] = {c: [] for c in categories}
    for element in raw.get("elements", []):
        tags = element.get("tags", {}) or {}
        cat, kind = categorize_element(tags)
        if cat is None or cat not in results:
            continue
        e_lat, e_lon = element_coords(element)
        if e_lat is None or e_lon is None:
            continue
        results[cat].append(
            {
                "name": tags.get("name"),
                "lat": e_lat,
                "lon": e_lon,
                "distance_m": round(haversine_m(lat, lon, e_lat, e_lon), 1),
                "kind": kind,
                "osm_id": element.get("id"),
                "osm_type": element.get("type"),
                "tags": {
                    k: v
                    for k, v in tags.items()
                    if k in ("name", "phone", "emergency", "operator", "ref", "addr:street", "addr:city")
                },
            }
        )

    for cat in results:
        results[cat].sort(key=lambda r: r["distance_m"])

    return {
        "center": {"lat": lat, "lon": lon},
        "radius_m": radius,
        "types": categories,
        "results": results,
        "counts": {c: len(v) for c, v in results.items()},
    }


def parse_types(arg: str) -> list[str]:
    if arg == "all":
        return ALL_CATEGORIES
    parts = [p.strip() for p in arg.split(",") if p.strip()]
    invalid = [p for p in parts if p not in CATEGORY_FILTERS]
    if invalid:
        raise argparse.ArgumentTypeError(
            f"Types inconnus : {invalid}. Valides : {ALL_CATEGORIES + ['all']}"
        )
    return parts


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Infrastructures critiques autour d'un point (OSM).")
    parser.add_argument("lat", type=float)
    parser.add_argument("lon", type=float)
    parser.add_argument("--radius", type=int, default=2000, help="Rayon en mètres (défaut 2000).")
    parser.add_argument("--types", type=parse_types, default=ALL_CATEGORIES, help="Catégories séparées par virgule, ou 'all'.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        out = fetch_infrastructure(args.lat, args.lon, args.radius, args.types)
    except urllib.error.URLError as e:
        print(json.dumps({"error": "network", "detail": str(e)}), file=sys.stderr)
        return 2
    except json.JSONDecodeError as e:
        print(json.dumps({"error": "invalid_response", "detail": str(e)}), file=sys.stderr)
        return 3

    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
