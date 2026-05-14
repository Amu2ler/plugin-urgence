"""Synthèse des risques majeurs d'une commune via l'API Géorisques (BRGM).

API publique, sans clé : https://www.georisques.gouv.fr/doc-api

Usage :
    python georisques.py <citycode_INSEE>
    python georisques.py 44109 --catnat-limit 5 --icpe-limit 10
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = "https://www.georisques.gouv.fr/api/v1"
TIMEOUT_S = 20

RADON_LABELS = {
    "1": "Faible",
    "2": "Moyen",
    "3": "Significatif",
}


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


def _safe(label: str, fn, default):
    try:
        return fn()
    except Exception as e:
        return {"_error": f"{type(e).__name__}: {e}", "_endpoint": label, **default}


def fetch_risques(citycode: str) -> dict:
    url = f"{BASE_URL}/gaspar/risques?code_insee={citycode}&page=1&page_size=5"
    data = _http_get_json(url)
    rows = data.get("data", []) or []
    if not rows:
        return {"commune": None, "risques_recenses": []}
    first = rows[0]
    items = first.get("risques_detail", []) or []
    return {
        "commune": first.get("libelle_commune"),
        "risques_recenses": [
            {"num": x.get("num_risque"), "label": x.get("libelle_risque_long")}
            for x in items
        ],
    }


def fetch_catnat(citycode: str, limit: int) -> dict:
    url = f"{BASE_URL}/gaspar/catnat?code_insee={citycode}&page=1&page_size={limit}"
    data = _http_get_json(url)
    rows = data.get("data", []) or []
    return {
        "total": data.get("results", len(rows)),
        "recent": [
            {
                "date_debut": x.get("date_debut_evt"),
                "date_fin": x.get("date_fin_evt"),
                "libelle": x.get("libelle_risque_jo"),
                "code_national": x.get("code_national_catnat"),
            }
            for x in rows
        ],
    }


def fetch_icpe(citycode: str, limit: int) -> dict:
    url = f"{BASE_URL}/installations_classees?code_insee={citycode}&page=1&page_size={limit}"
    data = _http_get_json(url)
    rows = data.get("data", []) or []
    return {
        "total": data.get("results", len(rows)),
        "exemples": [
            {
                "raison_sociale": x.get("raisonSociale"),
                "commune": x.get("commune"),
                "code_naf": x.get("codeNaf"),
                "lat": x.get("latitude"),
                "lon": x.get("longitude"),
                "elevage_bovins": x.get("bovins"),
                "elevage_porcs": x.get("porcs"),
                "elevage_volailles": x.get("volailles"),
                "carriere": x.get("carriere"),
                "eolienne": x.get("eolienne"),
                "industrie": x.get("industrie"),
            }
            for x in rows
        ],
    }


def fetch_radon(citycode: str) -> dict:
    url = f"{BASE_URL}/radon?code_insee={citycode}"
    data = _http_get_json(url)
    rows = data.get("data", []) or []
    if not rows:
        return {"classe_potentiel": None, "label": None}
    classe = rows[0].get("classe_potentiel")
    return {
        "classe_potentiel": int(classe) if classe and str(classe).isdigit() else classe,
        "label": RADON_LABELS.get(str(classe), "Inconnu"),
    }


def fetch_dicrim(citycode: str) -> dict:
    url = f"{BASE_URL}/gaspar/dicrim?code_insee={citycode}"
    data = _http_get_json(url)
    rows = data.get("data", []) or []
    if not rows:
        return {"publie": False, "annee_publication": None}
    return {
        "publie": True,
        "annee_publication": rows[0].get("annee_publication"),
    }


def build_report(citycode: str, catnat_limit: int, icpe_limit: int) -> dict:
    risques = _safe("risques", lambda: fetch_risques(citycode), {"risques_recenses": []})
    catnat = _safe("catnat", lambda: fetch_catnat(citycode, catnat_limit), {"total": 0, "recent": []})
    icpe = _safe("icpe", lambda: fetch_icpe(citycode, icpe_limit), {"total": 0, "exemples": []})
    radon = _safe("radon", lambda: fetch_radon(citycode), {"classe_potentiel": None, "label": None})
    dicrim = _safe("dicrim", lambda: fetch_dicrim(citycode), {"publie": False, "annee_publication": None})

    return {
        "code_insee": citycode,
        "commune": risques.get("commune"),
        "risques_recenses": risques.get("risques_recenses", []),
        "catnat": {"total": catnat.get("total", 0), "recent": catnat.get("recent", [])},
        "icpe": {"total": icpe.get("total", 0), "exemples": icpe.get("exemples", [])},
        "radon": {"classe_potentiel": radon.get("classe_potentiel"), "label": radon.get("label")},
        "dicrim": dicrim,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Synthèse risques majeurs Géorisques.")
    parser.add_argument("citycode", type=str, help="Code INSEE de la commune")
    parser.add_argument("--catnat-limit", type=int, default=10)
    parser.add_argument("--icpe-limit", type=int, default=5)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        out = build_report(args.citycode, args.catnat_limit, args.icpe_limit)
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
