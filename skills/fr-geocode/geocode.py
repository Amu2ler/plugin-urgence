"""Géocodage France via la Base Adresse Nationale (BAN).

API publique : https://api-adresse.data.gouv.fr/
Pas de clé requise. Quota : ~50 req/s/IP.

Usage :
    python geocode.py forward "12 rue de la Paix, 75002 Paris" [--limit N]
    python geocode.py reverse <lat> <lon>
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BAN_BASE_URL = "https://api-adresse.data.gouv.fr"
TIMEOUT_S = 20


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


def _format_feature(feature: dict) -> dict:
    props = feature.get("properties", {})
    coords = feature.get("geometry", {}).get("coordinates", [None, None])
    return {
        "label": props.get("label"),
        "lat": coords[1],
        "lon": coords[0],
        "score": props.get("score"),
        "postcode": props.get("postcode"),
        "city": props.get("city"),
        "citycode": props.get("citycode"),
        "context": props.get("context"),
        "type": props.get("type"),
    }


def forward(query: str, limit: int = 5) -> dict:
    params = urllib.parse.urlencode({"q": query, "limit": limit})
    data = _http_get_json(f"{BAN_BASE_URL}/search/?{params}")
    return {
        "query": query,
        "results": [_format_feature(f) for f in data.get("features", [])],
    }


def reverse(lat: float, lon: float) -> dict:
    params = urllib.parse.urlencode({"lat": lat, "lon": lon})
    data = _http_get_json(f"{BAN_BASE_URL}/reverse/?{params}")
    return {
        "query": {"lat": lat, "lon": lon},
        "results": [_format_feature(f) for f in data.get("features", [])],
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Géocodage France (BAN).")
    sub = parser.add_subparsers(dest="mode", required=True)

    p_fwd = sub.add_parser("forward", help="Adresse → coordonnées")
    p_fwd.add_argument("query", help="Adresse ou lieu en France")
    p_fwd.add_argument("--limit", type=int, default=5)

    p_rev = sub.add_parser("reverse", help="Coordonnées → adresse")
    p_rev.add_argument("lat", type=float)
    p_rev.add_argument("lon", type=float)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.mode == "forward":
            out = forward(args.query, limit=args.limit)
        else:
            out = reverse(args.lat, args.lon)
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
