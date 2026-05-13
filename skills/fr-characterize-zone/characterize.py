"""Caractérisation d'une zone : démographie commune + équipements sensibles.

Sources :
- geo.api.gouv.fr (INSEE) — population, surface, codes postaux
- Overpass / OpenStreetMap — EHPAD, écoles, crèches, hôpitaux

Usage :
    python characterize.py commune <citycode_INSEE>
    python characterize.py sensitive <lat> <lon> [--radius 2000]
    python characterize.py full <citycode_INSEE> <lat> <lon> [--radius 2000]
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import urllib.error
import urllib.parse
import urllib.request

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
GEO_API_BASE = "https://geo.api.gouv.fr"
TIMEOUT_S = 60

# Pondération vulnérabilité (occupants peu autonomes en cas d'urgence)
VULNERABILITY_WEIGHTS = {
    "ehpad": 3,
    "kindergarten": 3,
    "hospital": 2,
    "maternity": 2,
    "school": 1,
}


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6_371_000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmbd = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmbd / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _http_get_json(url: str) -> dict | list:
    req = urllib.request.Request(url, headers={"User-Agent": "plugin-urgence-fr/0.1"})
    with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _overpass_query(query: str) -> dict:
    data = urllib.parse.urlencode({"data": query}).encode("utf-8")
    req = urllib.request.Request(
        OVERPASS_URL,
        data=data,
        headers={"User-Agent": "plugin-urgence-fr/0.1"},
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT_S + 10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _element_coords(element: dict) -> tuple[float | None, float | None]:
    if element.get("type") == "node":
        return element.get("lat"), element.get("lon")
    center = element.get("center", {})
    return center.get("lat"), center.get("lon")


def commune_info(citycode: str) -> dict:
    """Récupère les infos démographiques d'une commune via geo.api.gouv.fr."""
    fields = "nom,code,codesPostaux,population,surface,centre"
    url = f"{GEO_API_BASE}/communes/{citycode}?fields={fields}"
    data = _http_get_json(url)
    if not isinstance(data, dict):
        return {"error": "commune_not_found", "code": citycode}

    population = data.get("population")
    surface_ha = data.get("surface")  # geo.api.gouv.fr renvoie en hectares
    surface_km2 = round(surface_ha / 100.0, 2) if surface_ha else None
    densite = round(population / surface_km2, 1) if (population and surface_km2) else None

    return {
        "code": data.get("code"),
        "nom": data.get("nom"),
        "population": population,
        "surface_km2": surface_km2,
        "densite_hab_km2": densite,
        "codes_postaux": data.get("codesPostaux", []),
        "centre": data.get("centre"),
    }


def sensitive_facilities(lat: float, lon: float, radius: int) -> dict:
    """Équipements sensibles autour d'un point (EHPAD, écoles, crèches, hôpitaux)."""
    query = f"""[out:json][timeout:{TIMEOUT_S}];
(
  node["amenity"="social_facility"]["social_facility"="nursing_home"](around:{radius},{lat},{lon});
  way["amenity"="social_facility"]["social_facility"="nursing_home"](around:{radius},{lat},{lon});
  node["amenity"="social_facility"]["social_facility"="assisted_living"](around:{radius},{lat},{lon});
  way["amenity"="social_facility"]["social_facility"="assisted_living"](around:{radius},{lat},{lon});
  node["amenity"="kindergarten"](around:{radius},{lat},{lon});
  way["amenity"="kindergarten"](around:{radius},{lat},{lon});
  node["amenity"="school"](around:{radius},{lat},{lon});
  way["amenity"="school"](around:{radius},{lat},{lon});
  node["amenity"="hospital"](around:{radius},{lat},{lon});
  way["amenity"="hospital"](around:{radius},{lat},{lon});
  node["healthcare"="hospital"](around:{radius},{lat},{lon});
  way["healthcare"="hospital"](around:{radius},{lat},{lon});
);
out center tags;"""

    raw = _overpass_query(query)
    buckets: dict[str, list[dict]] = {
        "ehpad": [],
        "kindergarten": [],
        "school": [],
        "hospital": [],
        "maternity": [],
    }

    for element in raw.get("elements", []):
        tags = element.get("tags", {}) or {}
        e_lat, e_lon = _element_coords(element)
        if e_lat is None or e_lon is None:
            continue

        # Classification
        social = tags.get("social_facility")
        amenity = tags.get("amenity")
        healthcare = tags.get("healthcare")

        if social in ("nursing_home", "assisted_living"):
            bucket = "ehpad"
        elif amenity == "kindergarten":
            bucket = "kindergarten"
        elif amenity == "school":
            bucket = "school"
        elif healthcare == "maternity" or tags.get("healthcare:speciality") == "maternity":
            bucket = "maternity"
        elif amenity == "hospital" or healthcare == "hospital":
            bucket = "hospital"
        else:
            continue

        buckets[bucket].append(
            {
                "name": tags.get("name"),
                "lat": e_lat,
                "lon": e_lon,
                "distance_m": round(haversine_m(lat, lon, e_lat, e_lon), 1),
                "osm_id": element.get("id"),
                "osm_type": element.get("type"),
                "tags": {
                    k: v
                    for k, v in tags.items()
                    if k in ("name", "operator", "capacity", "phone", "addr:street", "addr:city")
                },
            }
        )

    for k in buckets:
        buckets[k].sort(key=lambda r: r["distance_m"])

    score = sum(VULNERABILITY_WEIGHTS[k] * len(v) for k, v in buckets.items())

    return {
        "center": {"lat": lat, "lon": lon},
        "radius_m": radius,
        "results": buckets,
        "counts": {k: len(v) for k, v in buckets.items()},
        "vulnerability_score": score,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Caractérisation de zone (démographie + équipements sensibles).")
    sub = parser.add_subparsers(dest="mode", required=True)

    p_c = sub.add_parser("commune", help="Démographie d'une commune (INSEE)")
    p_c.add_argument("citycode", type=str)

    p_s = sub.add_parser("sensitive", help="Équipements sensibles autour d'un point")
    p_s.add_argument("lat", type=float)
    p_s.add_argument("lon", type=float)
    p_s.add_argument("--radius", type=int, default=2000)

    p_f = sub.add_parser("full", help="Démographie + équipements sensibles")
    p_f.add_argument("citycode", type=str)
    p_f.add_argument("lat", type=float)
    p_f.add_argument("lon", type=float)
    p_f.add_argument("--radius", type=int, default=2000)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.mode == "commune":
            out = commune_info(args.citycode)
        elif args.mode == "sensitive":
            out = sensitive_facilities(args.lat, args.lon, args.radius)
        else:  # full
            out = {
                "commune": commune_info(args.citycode),
                "sensitive": sensitive_facilities(args.lat, args.lon, args.radius),
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
