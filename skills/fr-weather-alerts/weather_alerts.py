"""Prévisions météo + niveau d'alerte calculé sur seuils (Open-Meteo).

Open-Meteo : API gratuite, sans clé. https://open-meteo.com/

Usage :
    python weather_alerts.py <lat> <lon> [--days 3]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
TIMEOUT_S = 15

LEVELS = ["green", "yellow", "orange", "red"]


def _http_get_json(url: str, retries: int = 2) -> dict:
    """GET JSON avec retry exponentiel sur timeout, 5xx et 429."""
    last_err: Exception | None = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "plugin-urgence-fr/0.3"})
            with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            last_err = e
            if e.code in (429, 502, 503, 504) and attempt < retries:
                time.sleep(2 ** attempt)
                continue
            raise
        except (urllib.error.URLError, TimeoutError) as e:
            last_err = e
            if attempt < retries:
                time.sleep(1.5 ** attempt)
                continue
            raise
    raise last_err if last_err else RuntimeError("retries exhausted")


def _classify(value: float, thresholds: tuple[float, float, float], reverse: bool = False) -> str:
    """thresholds = (yellow, orange, red). reverse=True pour les seuils décroissants (froid)."""
    y, o, r = thresholds
    if reverse:
        if value <= r:
            return "red"
        if value <= o:
            return "orange"
        if value <= y:
            return "yellow"
        return "green"
    else:
        if value >= r:
            return "red"
        if value >= o:
            return "orange"
        if value >= y:
            return "yellow"
        return "green"


def _max_level(levels: list[str]) -> str:
    """Renvoie le niveau d'alerte le plus élevé."""
    return max(levels, key=lambda lv: LEVELS.index(lv)) if levels else "green"


def fetch_weather(lat: float, lon: float, days: int) -> dict:
    params = urllib.parse.urlencode(
        {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,wind_speed_10m,wind_gusts_10m,precipitation,weather_code",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,snowfall_sum,wind_speed_10m_max,wind_gusts_10m_max,weather_code",
            "wind_speed_unit": "kmh",
            "timezone": "Europe/Paris",
            "forecast_days": days,
        }
    )
    return _http_get_json(f"{OPEN_METEO_URL}?{params}")


def compute_alerts(daily: dict) -> dict:
    """Calcule les niveaux d'alerte à partir des prévisions journalières."""
    dates = daily.get("time", [])
    gusts = daily.get("wind_gusts_10m_max", [])
    rains = daily.get("precipitation_sum", [])
    snows = daily.get("snowfall_sum", [])
    tmaxs = daily.get("temperature_2m_max", [])
    tmins = daily.get("temperature_2m_min", [])

    def _argmax(values: list[float | None]) -> int | None:
        clean = [(i, v) for i, v in enumerate(values) if v is not None]
        return max(clean, key=lambda iv: iv[1])[0] if clean else None

    def _argmin(values: list[float | None]) -> int | None:
        clean = [(i, v) for i, v in enumerate(values) if v is not None]
        return min(clean, key=lambda iv: iv[1])[0] if clean else None

    def _val(values: list, idx: int | None):
        return values[idx] if idx is not None and idx < len(values) else None

    i_gust = _argmax(gusts)
    i_rain = _argmax(rains)
    i_snow = _argmax(snows) if snows else None
    i_heat = _argmax(tmaxs)
    i_cold = _argmin(tmins)

    alerts = {
        "wind": {
            "level": _classify(_val(gusts, i_gust) or 0, (70, 100, 130)),
            "max_gust_kmh": _val(gusts, i_gust),
            "day": _val(dates, i_gust),
        },
        "rain": {
            "level": _classify(_val(rains, i_rain) or 0, (30, 50, 100)),
            "max_mm": _val(rains, i_rain),
            "day": _val(dates, i_rain),
        },
        "snow": {
            "level": _classify(_val(snows, i_snow) or 0, (3, 10, 20)) if i_snow is not None else "green",
            "max_cm": _val(snows, i_snow) if i_snow is not None else 0,
            "day": _val(dates, i_snow),
        },
        "heat": {
            "level": _classify(_val(tmaxs, i_heat) or 0, (32, 36, 40)),
            "max_tmax": _val(tmaxs, i_heat),
            "day": _val(dates, i_heat),
        },
        "cold": {
            "level": _classify(_val(tmins, i_cold) or 0, (-5, -10, -15), reverse=True),
            "min_tmin": _val(tmins, i_cold),
            "day": _val(dates, i_cold),
        },
    }
    overall = _max_level([a["level"] for a in alerts.values()])
    return alerts, overall


def build_report(lat: float, lon: float, days: int) -> dict:
    data = fetch_weather(lat, lon, days)
    daily = data.get("daily", {})

    daily_list = []
    for i, d in enumerate(daily.get("time", [])):
        daily_list.append(
            {
                "date": d,
                "tmin": (daily.get("temperature_2m_min") or [None])[i],
                "tmax": (daily.get("temperature_2m_max") or [None])[i],
                "precipitation_mm": (daily.get("precipitation_sum") or [None])[i],
                "snowfall_cm": (daily.get("snowfall_sum") or [None])[i],
                "wind_max_kmh": (daily.get("wind_speed_10m_max") or [None])[i],
                "gust_max_kmh": (daily.get("wind_gusts_10m_max") or [None])[i],
                "weather_code": (daily.get("weather_code") or [None])[i],
            }
        )

    alerts, overall = compute_alerts(daily)

    return {
        "location": {"lat": lat, "lon": lon},
        "current": data.get("current"),
        "daily": daily_list,
        "alerts": alerts,
        "overall_level": overall,
        "vigilance_url": "https://vigilance.meteofrance.fr/",
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Météo + alertes (Open-Meteo).")
    parser.add_argument("lat", type=float)
    parser.add_argument("lon", type=float)
    parser.add_argument("--days", type=int, default=3, help="Nombre de jours de prévision (1-16).")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        out = build_report(args.lat, args.lon, args.days)
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
