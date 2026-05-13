"""Accès à l'eau : points d'eau OSM + qualité eau potable Hub'Eau.

Sources :
- Overpass (OpenStreetMap) — points d'eau physiques
- Hub'Eau — https://hubeau.eaufrance.fr/page/api-qualite-eau-potable

Usage :
    python water_access.py osm <lat> <lon> [--radius 1000]
    python water_access.py quality <citycode_INSEE> [--limit 20]
    python water_access.py all <lat> <lon> <citycode_INSEE> [--radius 1500]
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
HUBEAU_BASE = "https://hubeau.eaufrance.fr/api/v1/qualite_eau_potable"
TIMEOUT_S = 60


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6_371_000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmbd = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmbd / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _overpass_query(query: str) -> dict:
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


def _http_get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "plugin-urgence-fr/0.1"})
    with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _element_coords(element: dict) -> tuple[float | None, float | None]:
    if element.get("type") == "node":
        return element.get("lat"), element.get("lon")
    center = element.get("center", {})
    return center.get("lat"), center.get("lon")


def osm_water(lat: float, lon: float, radius: int) -> dict:
    """Points d'eau OSM dans un rayon donné."""
    query = f"""[out:json][timeout:{TIMEOUT_S}];
(
  node["amenity"="drinking_water"](around:{radius},{lat},{lon});
  node["man_made"="water_tap"](around:{radius},{lat},{lon});
  node["man_made"="water_well"](around:{radius},{lat},{lon});
  node["man_made"="water_tower"](around:{radius},{lat},{lon});
  way["man_made"="water_tower"](around:{radius},{lat},{lon});
  node["natural"="spring"](around:{radius},{lat},{lon});
  way["natural"="water"](around:{radius},{lat},{lon});
  relation["natural"="water"](around:{radius},{lat},{lon});
  way["waterway"~"^(river|stream|canal)$"](around:{radius},{lat},{lon});
);
out center tags;"""

    raw = _overpass_query(query)
    buckets: dict[str, list[dict]] = {
        "drinking_water": [],
        "water_tower": [],
        "surface_water": [],
        "spring": [],
    }

    for element in raw.get("elements", []):
        tags = element.get("tags", {}) or {}
        e_lat, e_lon = _element_coords(element)
        if e_lat is None or e_lon is None:
            continue

        if tags.get("amenity") == "drinking_water" or tags.get("man_made") in ("water_tap", "water_well"):
            bucket = "drinking_water"
            kind = tags.get("amenity") or tags.get("man_made")
        elif tags.get("man_made") == "water_tower":
            bucket = "water_tower"
            kind = "water_tower"
        elif tags.get("natural") == "spring":
            bucket = "spring"
            kind = "spring"
        elif tags.get("natural") == "water" or tags.get("waterway"):
            bucket = "surface_water"
            kind = tags.get("waterway") or tags.get("water") or "water"
        else:
            continue

        buckets[bucket].append(
            {
                "name": tags.get("name"),
                "lat": e_lat,
                "lon": e_lon,
                "distance_m": round(haversine_m(lat, lon, e_lat, e_lon), 1),
                "kind": kind,
                "osm_id": element.get("id"),
                "osm_type": element.get("type"),
            }
        )

    for k in buckets:
        buckets[k].sort(key=lambda r: r["distance_m"])

    return {
        "center": {"lat": lat, "lon": lon},
        "radius_m": radius,
        "results": buckets,
        "counts": {k: len(v) for k, v in buckets.items()},
    }


def water_quality(citycode: str, limit: int = 20) -> dict:
    """Qualité de l'eau potable distribuée pour une commune (INSEE)."""
    params = urllib.parse.urlencode({"code_commune": citycode, "size": limit})
    url = f"{HUBEAU_BASE}/resultats_dis?{params}"
    data = _http_get_json(url)

    samples = data.get("data", []) or []

    def _is_non_conforme(s: dict) -> bool:
        text = (s.get("conclusion_conformite_prelevement") or "").lower()
        return "non conforme" in text or "non-conforme" in text

    non_conf = sum(1 for s in samples if _is_non_conforme(s))
    latest = samples[0].get("date_prelevement") if samples else None

    cleaned = [
        {
            "date_prelevement": s.get("date_prelevement"),
            "conclusion_conformite_prelevement": s.get("conclusion_conformite_prelevement"),
            "conclusion_conformite_bacterio_prelevement": s.get("conclusion_conformite_bacterio_prelevement"),
            "conclusion_conformite_chimique_prelevement": s.get("conclusion_conformite_chimique_prelevement"),
            "nom_uge": s.get("nom_uge"),
            "nom_distributeur": s.get("nom_distributeur"),
            "nom_moa": s.get("nom_moa"),
        }
        for s in samples
    ]

    return {
        "citycode": citycode,
        "sample_count": len(samples),
        "latest_sample_date": latest,
        "non_conformities": non_conf,
        "samples": cleaned,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Accès à l'eau (OSM + Hub'Eau).")
    sub = parser.add_subparsers(dest="mode", required=True)

    p_osm = sub.add_parser("osm", help="Points d'eau OSM autour d'un point")
    p_osm.add_argument("lat", type=float)
    p_osm.add_argument("lon", type=float)
    p_osm.add_argument("--radius", type=int, default=1000)

    p_q = sub.add_parser("quality", help="Qualité eau potable pour une commune (INSEE)")
    p_q.add_argument("citycode", type=str)
    p_q.add_argument("--limit", type=int, default=20)

    p_all = sub.add_parser("all", help="OSM + qualité en une commande")
    p_all.add_argument("lat", type=float)
    p_all.add_argument("lon", type=float)
    p_all.add_argument("citycode", type=str)
    p_all.add_argument("--radius", type=int, default=1500)
    p_all.add_argument("--limit", type=int, default=20)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.mode == "osm":
            out = osm_water(args.lat, args.lon, args.radius)
        elif args.mode == "quality":
            out = water_quality(args.citycode, limit=args.limit)
        else:  # all
            out = {
                "osm": osm_water(args.lat, args.lon, args.radius),
                "quality": water_quality(args.citycode, limit=args.limit),
            }
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
