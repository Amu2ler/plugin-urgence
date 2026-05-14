"""Surveillance épidémiologique en France via le Réseau Sentinelles (Sentiweb).

API publique : https://www.sentiweb.fr/api/v1/datasets/rest/
Pas de clé. Quota raisonnable mais 429 possible si trop d'appels rapprochés.

Usage :
    python sentinelles.py national [--indicators 1,3,7]
    python sentinelles.py region <code_region_INSEE> [--indicators 1,3,7]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://www.sentiweb.fr/api/v1/datasets/rest"
TIMEOUT_S = 15

# Libellés et IDs des indicateurs Sentinelles fréquemment suivis.
INDICATOR_LABELS = {
    "1": "Syndromes grippaux",
    "3": "Diarrhée aiguë",
    "7": "Varicelle",
    "12": "Maladie de Lyme",
    "25": "Acutisation respiratoire",
}

DEFAULT_INDICATORS = ["1", "3", "7"]

LEVELS = ["green", "yellow", "orange", "red"]


def _http_get_json(url: str, retries: int = 2) -> dict:
    last_err: Exception | None = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "plugin-urgence-fr/0.2", "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            last_err = e
            if e.code in (429, 502, 503, 504) and attempt < retries:
                time.sleep(1 + attempt * 2)
                continue
            raise
        except (urllib.error.URLError, TimeoutError) as e:
            last_err = e
            if attempt < retries:
                time.sleep(1)
                continue
            raise
    raise last_err if last_err else RuntimeError("Sentiweb: échec après retries")


def _classify(inc100: float | None) -> str:
    if inc100 is None:
        return "green"
    if inc100 >= 200:
        return "red"
    if inc100 >= 100:
        return "orange"
    if inc100 >= 50:
        return "yellow"
    return "green"


def _max_level(levels: list[str]) -> str:
    return max(levels, key=lambda lv: LEVELS.index(lv)) if levels else "green"


def fetch_indicator(indicator_id: str, geo_level: str = "PAY") -> list[dict]:
    """Récupère la dernière observation pour un indicateur, au niveau géographique demandé."""
    params = urllib.parse.urlencode({"indicator": indicator_id, "geo": geo_level, "span": "last"})
    data = _http_get_json(f"{BASE}/incidence?{params}")
    return data.get("data", []) or []


def build_report(mode: str, geo_filter: str | None, indicators: list[str]) -> dict:
    """mode = 'national' ou 'region'. geo_filter = code INSEE région si mode regional."""
    geo_level = "PAY" if mode == "national" else "RDD"
    indicator_blocks: list[dict] = []
    week_iso = None

    for ind_id in indicators:
        try:
            rows = fetch_indicator(ind_id, geo_level=geo_level)
        except Exception as e:
            indicator_blocks.append({
                "id": ind_id,
                "label": INDICATOR_LABELS.get(ind_id, "Inconnu"),
                "error": f"{type(e).__name__}: {e}",
            })
            continue

        # filtre régional si nécessaire
        if mode == "region" and geo_filter:
            rows = [r for r in rows if str(r.get("geo_insee")) == str(geo_filter)]

        for r in rows:
            week_iso = r.get("week") or week_iso
            inc100 = r.get("inc100")
            indicator_blocks.append({
                "id": str(r.get("indicator")),
                "label": INDICATOR_LABELS.get(str(r.get("indicator")), "Indicateur " + str(r.get("indicator"))),
                "geo_insee": r.get("geo_insee"),
                "geo_name": r.get("geo_name"),
                "inc": r.get("inc"),
                "inc100": inc100,
                "inc100_low": r.get("inc100_low"),
                "inc100_up": r.get("inc100_up"),
                "level": _classify(inc100),
            })

        # anti-rate-limit : Sentiweb répond 429 si requêtes trop rapprochées
        time.sleep(1.0)

    overall = _max_level([b["level"] for b in indicator_blocks if "level" in b])

    return {
        "geo_level": geo_level,
        "geo_filter": geo_filter,
        "week_iso": week_iso,
        "indicators": indicator_blocks,
        "overall_level": overall,
        "source": "https://www.sentiweb.fr/",
    }


def _parse_indicators(arg: str) -> list[str]:
    parts = [p.strip() for p in arg.split(",") if p.strip()]
    if not parts:
        raise argparse.ArgumentTypeError("Liste d'indicateurs vide.")
    return parts


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Surveillance épidémiologique Sentinelles.")
    sub = parser.add_subparsers(dest="mode", required=True)

    p_nat = sub.add_parser("national", help="Niveau national")
    p_nat.add_argument("--indicators", type=_parse_indicators, default=DEFAULT_INDICATORS)

    p_reg = sub.add_parser("region", help="Niveau régional (code INSEE région à 2 chiffres)")
    p_reg.add_argument("region_code", type=str)
    p_reg.add_argument("--indicators", type=_parse_indicators, default=DEFAULT_INDICATORS)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.mode == "national":
            out = build_report("national", None, args.indicators)
        else:
            out = build_report("region", args.region_code, args.indicators)
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
