"""Niveaux d'eau temps réel des cours d'eau via Hub'Eau Hydrométrie.

API officielle Hub'Eau : https://hubeau.eaufrance.fr/page/api-hydrometrie

Usage :
    python vigicrues.py <lat> <lon> [--radius-km 15] [--limit 10]
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

HUBEAU_BASE = "https://hubeau.eaufrance.fr/api/v2/hydrometrie"
TIMEOUT_S = 20


def _http_get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "plugin-urgence-fr/0.1"})
    with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
        return json.loads(resp.read().decode("utf-8"))


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmbd = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmbd / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def fetch_stations(lat: float, lon: float, radius_km: int, limit: int) -> list[dict]:
    params = urllib.parse.urlencode(
        {
            "longitude": lon,
            "latitude": lat,
            "distance": radius_km,
            "en_service": "true",
            "size": limit,
            "format": "json",
        }
    )
    data = _http_get_json(f"{HUBEAU_BASE}/referentiel/stations?{params}")
    return data.get("data", []) or []


def fetch_observations(code_station: str, size: int = 150) -> list[dict]:
    """Renvoie les observations récentes de hauteur (H) pour une station."""
    params = urllib.parse.urlencode(
        {
            "code_entite": code_station,
            "grandeur_hydro": "H",
            "size": size,
            "fields": "date_obs,resultat_obs,grandeur_hydro",
        }
    )
    data = _http_get_json(f"{HUBEAU_BASE}/observations_tr?{params}")
    return data.get("data", []) or []


def _parse_iso(s: str) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def compute_trend(observations: list[dict]) -> tuple[float | None, str, float | None]:
    """Calcule la tendance ~24h. Retourne (latest_height_m, trend, delta_m)."""
    if not observations:
        return None, "unknown", None

    obs_sorted = sorted(
        [o for o in observations if o.get("resultat_obs") is not None and o.get("date_obs")],
        key=lambda o: o["date_obs"],
    )
    if not obs_sorted:
        return None, "unknown", None

    latest = obs_sorted[-1]
    latest_height_m = round(latest["resultat_obs"] / 1000.0, 3)  # mm -> m
    latest_dt = _parse_iso(latest["date_obs"])
    if latest_dt is None:
        return latest_height_m, "unknown", None

    target_dt = latest_dt.timestamp() - 24 * 3600
    # Cherche l'observation la plus proche de "il y a 24h"
    closest = None
    best_diff = float("inf")
    for o in obs_sorted:
        dt = _parse_iso(o["date_obs"])
        if dt is None:
            continue
        diff = abs(dt.timestamp() - target_dt)
        if diff < best_diff:
            best_diff = diff
            closest = o

    if closest is None or best_diff > 6 * 3600:  # tolérance ±6h
        return latest_height_m, "unknown", None

    older_m = round(closest["resultat_obs"] / 1000.0, 3)
    delta = round(latest_height_m - older_m, 3)
    if delta > 0.05:
        trend = "rising"
    elif delta < -0.05:
        trend = "falling"
    else:
        trend = "stable"
    return latest_height_m, trend, delta


def build_report(lat: float, lon: float, radius_km: int, limit: int) -> dict:
    stations = fetch_stations(lat, lon, radius_km, limit)
    out_stations = []
    for s in stations:
        s_lat = s.get("latitude_station")
        s_lon = s.get("longitude_station")
        code_station = s.get("code_station")
        if s_lat is None or s_lon is None or not code_station:
            continue
        try:
            obs = fetch_observations(code_station)
        except Exception:
            obs = []
        latest_h, trend, delta = compute_trend(obs)
        latest_obs_date = obs[0].get("date_obs") if obs else None

        out_stations.append(
            {
                "code_station": code_station,
                "libelle": s.get("libelle_station"),
                "cours_eau": s.get("libelle_cours_eau"),
                "commune": s.get("libelle_commune"),
                "lat": s_lat,
                "lon": s_lon,
                "distance_km": round(haversine_km(lat, lon, s_lat, s_lon), 2),
                "latest_height_m": latest_h,
                "latest_obs_date": latest_obs_date,
                "trend_24h": trend,
                "delta_24h_m": delta,
            }
        )

    out_stations.sort(key=lambda x: x["distance_km"])

    return {
        "search": {"lat": lat, "lon": lon, "radius_km": radius_km},
        "stations_count": len(out_stations),
        "stations": out_stations,
        "vigicrues_url": "https://www.vigicrues.gouv.fr/",
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Niveaux d'eau cours d'eau (Hub'Eau).")
    parser.add_argument("lat", type=float)
    parser.add_argument("lon", type=float)
    parser.add_argument("--radius-km", type=int, default=15)
    parser.add_argument("--limit", type=int, default=10)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        out = build_report(args.lat, args.lon, args.radius_km, args.limit)
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
