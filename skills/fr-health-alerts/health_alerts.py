"""Alertes sanitaires : qualité de l'air + pollens (Open-Meteo Air Quality).

Open-Meteo Air Quality : gratuit, sans clé.
https://open-meteo.com/en/docs/air-quality-api

Usage :
    python health_alerts.py <lat> <lon>
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
TIMEOUT_S = 15

LEVELS = ["green", "yellow", "orange", "red"]

POLLEN_FIELDS = [
    "alder_pollen",
    "birch_pollen",
    "grass_pollen",
    "mugwort_pollen",
    "olive_pollen",
    "ragweed_pollen",
]


def _http_get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "plugin-urgence-fr/0.1"})
    with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _max_level(levels: list[str]) -> str:
    return max(levels, key=lambda lv: LEVELS.index(lv)) if levels else "green"


def _classify_aqi(aqi: float | None) -> str:
    if aqi is None:
        return "green"
    if aqi >= 80:
        return "red"
    if aqi >= 60:
        return "orange"
    if aqi >= 40:
        return "yellow"
    return "green"


def _classify_pollen(value: float | None) -> str:
    if value is None:
        return "green"
    if value >= 100:
        return "red"
    if value >= 30:
        return "orange"
    if value >= 5:
        return "yellow"
    return "green"


def fetch_air_quality(lat: float, lon: float) -> dict:
    current_vars = ",".join(
        [
            "european_aqi",
            "pm10",
            "pm2_5",
            "carbon_monoxide",
            "nitrogen_dioxide",
            "sulphur_dioxide",
            "ozone",
        ]
        + POLLEN_FIELDS
    )
    params = urllib.parse.urlencode(
        {
            "latitude": lat,
            "longitude": lon,
            "current": current_vars,
            "timezone": "Europe/Paris",
        }
    )
    return _http_get_json(f"{AIR_QUALITY_URL}?{params}")


def build_report(lat: float, lon: float) -> dict:
    data = fetch_air_quality(lat, lon)
    current = data.get("current", {}) or {}

    aqi = current.get("european_aqi")
    aqi_level = _classify_aqi(aqi)

    pollutants = {
        "pm2_5_ug_m3": current.get("pm2_5"),
        "pm10_ug_m3": current.get("pm10"),
        "nitrogen_dioxide_ug_m3": current.get("nitrogen_dioxide"),
        "ozone_ug_m3": current.get("ozone"),
        "sulphur_dioxide_ug_m3": current.get("sulphur_dioxide"),
        "carbon_monoxide_ug_m3": current.get("carbon_monoxide"),
    }

    pollen_values: dict[str, float | None] = {f: current.get(f) for f in POLLEN_FIELDS}
    pollen_levels = {f: _classify_pollen(v) for f, v in pollen_values.items()}
    pollen_overall = _max_level(list(pollen_levels.values()))
    # dominant = pollen le plus concentré (s'il y a une valeur)
    valid = [(f, v) for f, v in pollen_values.items() if v is not None]
    dominant = max(valid, key=lambda fv: fv[1])[0].replace("_pollen", "") if valid else None

    pollen_out = {f.replace("_pollen", "_grain_m3"): v for f, v in pollen_values.items()}
    pollen_out["level"] = pollen_overall
    pollen_out["dominant"] = dominant

    overall = _max_level([aqi_level, pollen_overall])

    return {
        "location": {"lat": lat, "lon": lon},
        "time": current.get("time"),
        "air_quality": {
            "european_aqi": aqi,
            "level": aqi_level,
            "pollutants": pollutants,
        },
        "pollen": pollen_out,
        "overall_level": overall,
        "references": {
            "sante_publique_france": "https://www.santepubliquefrance.fr/",
            "atmo_france": "https://www.atmo-france.org/",
            "pollens_rnsa": "https://www.pollens.fr/",
        },
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Alertes sanitaires (air + pollens).")
    parser.add_argument("lat", type=float)
    parser.add_argument("lon", type=float)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        out = build_report(args.lat, args.lon)
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
