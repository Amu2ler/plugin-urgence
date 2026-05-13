"""Itinéraires routiers via OSRM (Open Source Routing Machine).

Serveur public démo : https://router.project-osrm.org/  (gratuit, sans clé)

Usage :
    python route.py route <lat1> <lon1> <lat2> <lon2>
    python route.py routes <lat> <lon> "<lat,lon[,label]>" ["<lat,lon[,label]>" ...]
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

OSRM_BASE = "https://router.project-osrm.org/route/v1/driving"
TIMEOUT_S = 20


def _http_get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "plugin-urgence-fr/0.1"})
    with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _human_duration(seconds: float) -> str:
    s = int(round(seconds))
    if s < 60:
        return f"{s} s"
    m, s = divmod(s, 60)
    if m < 60:
        return f"{m} min"
    h, m = divmod(m, 60)
    return f"{h} h {m:02d}"


def osrm_route(
    from_lat: float,
    from_lon: float,
    to_lat: float,
    to_lon: float,
    overview: str = "simplified",
) -> dict:
    """Itinéraire OSRM entre deux points. Renvoie distance/duration/geometry."""
    coords = f"{from_lon},{from_lat};{to_lon},{to_lat}"
    params = urllib.parse.urlencode({"overview": overview, "geometries": "geojson"})
    data = _http_get_json(f"{OSRM_BASE}/{coords}?{params}")
    if data.get("code") != "Ok" or not data.get("routes"):
        return {"error": "osrm_failed", "detail": data.get("code"), "message": data.get("message")}
    route = data["routes"][0]
    return {
        "from": {"lat": from_lat, "lon": from_lon},
        "to": {"lat": to_lat, "lon": to_lon},
        "distance_m": round(route["distance"], 1),
        "duration_s": round(route["duration"], 1),
        "duration_human": _human_duration(route["duration"]),
        "geometry": route.get("geometry"),
    }


def osrm_routes(from_lat: float, from_lon: float, destinations: list[dict]) -> dict:
    """Plusieurs itinéraires depuis un point, triés par durée."""
    results: list[dict] = []
    for d in destinations:
        r = osrm_route(from_lat, from_lon, d["lat"], d["lon"], overview="false")
        if "error" in r:
            results.append({"label": d.get("label"), "to": {"lat": d["lat"], "lon": d["lon"]}, "error": r["error"]})
            continue
        results.append(
            {
                "label": d.get("label"),
                "to": r["to"],
                "distance_m": r["distance_m"],
                "duration_s": r["duration_s"],
                "duration_human": r["duration_human"],
            }
        )

    results.sort(key=lambda x: x.get("duration_s") or float("inf"))
    return {"from": {"lat": from_lat, "lon": from_lon}, "results": results}


def _parse_destination(spec: str) -> dict:
    """Parse "lat,lon" ou "lat,lon,label libre"."""
    parts = spec.split(",", 2)
    if len(parts) < 2:
        raise argparse.ArgumentTypeError(f"Destination invalide : {spec!r} (attendu : 'lat,lon[,label]')")
    try:
        lat = float(parts[0])
        lon = float(parts[1])
    except ValueError as e:
        raise argparse.ArgumentTypeError(f"Coordonnées invalides dans {spec!r}: {e}") from e
    return {"lat": lat, "lon": lon, "label": parts[2].strip() if len(parts) == 3 else None}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Itinéraires routiers (OSRM).")
    sub = parser.add_subparsers(dest="mode", required=True)

    p_r = sub.add_parser("route", help="Itinéraire A -> B")
    p_r.add_argument("from_lat", type=float)
    p_r.add_argument("from_lon", type=float)
    p_r.add_argument("to_lat", type=float)
    p_r.add_argument("to_lon", type=float)

    p_rs = sub.add_parser("routes", help="A -> plusieurs destinations, triees par duree")
    p_rs.add_argument("from_lat", type=float)
    p_rs.add_argument("from_lon", type=float)
    p_rs.add_argument("destinations", nargs="+", type=_parse_destination)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.mode == "route":
            out = osrm_route(args.from_lat, args.from_lon, args.to_lat, args.to_lon)
        else:
            out = osrm_routes(args.from_lat, args.from_lon, args.destinations)
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
