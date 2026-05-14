"""Script de démo : orchestration des 10 skills du plugin sur un scénario d'urgence.

Scénario : "Incendie signalé au 29 rue de Strasbourg, 44000 Nantes."
L'agent doit construire un contexte décisionnel complet.

Usage :
    python demo.py
    python demo.py --address "10 rue de la Paix, 75002 Paris"
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

SKILLS_DIR = Path(__file__).parent / "skills"


def _safe(label: str, fn, *args, **kwargs):
    """Exécute fn(*args, **kwargs) en attrapant toute exception et en signalant l'erreur."""
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        print(f"  [!] Échec de {label}: {type(e).__name__}: {e}")
        return None


def _load_module(skill: str, filename: str):
    """Charge dynamiquement un module à partir de skills/<skill>/<filename>."""
    path = SKILLS_DIR / skill / filename
    spec = importlib.util.spec_from_file_location(f"plugin_urgence.{skill}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Impossible de charger {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _print_section(title: str) -> None:
    print()
    print("=" * 70)
    print(f"  {title}")
    print("=" * 70)


def _short_json(obj, max_keys: int = 5) -> str:
    """Affichage compact pour la démo."""
    return json.dumps(obj, ensure_ascii=False, indent=2)[:1500]


def run_scenario(address: str) -> None:
    print(f"\nScénario : situation d'urgence à l'adresse")
    print(f"  >>> {address}")
    print("\nL'agent enchaîne les 10 skills du plugin pour construire le contexte.")

    # 1. Géocodage
    _print_section("1. fr-geocode — Localiser l'adresse")
    geocode = _load_module("fr-geocode", "geocode.py")
    g = _safe("fr-geocode", geocode.forward, address, limit=1)
    if not g or not g.get("results"):
        print("  [!] Géocodage indisponible — étapes suivantes impossibles. Abandon.")
        return
    loc = g["results"][0]
    lat, lon, citycode, label = loc["lat"], loc["lon"], loc["citycode"], loc["label"]
    print(f"  Adresse résolue : {label}")
    print(f"  Coordonnées     : {lat}, {lon}")
    print(f"  Code INSEE      : {citycode}  (score={loc['score']:.2f})")

    # 2. Infrastructures critiques
    _print_section("2. fr-locate-infra — Hôpitaux et secours dans 2 km")
    locate = _load_module("fr-locate-infra", "locate_infra.py")
    infra = _safe("fr-locate-infra", locate.fetch_infrastructure, lat, lon, radius=2000, categories=["health", "emergency"])
    if infra:
        print(f"  {infra['counts']['health']} structures de santé, {infra['counts']['emergency']} de secours")
        print("  Top 3 santé :")
        for x in infra["results"]["health"][:3]:
            print(f"    - {x['name'] or '(sans nom)'} [{x['kind']}] à {x['distance_m']:.0f} m")
        print("  Top 3 secours :")
        for x in infra["results"]["emergency"][:3]:
            print(f"    - {x['name'] or '(sans nom)'} [{x['kind']}] à {x['distance_m']:.0f} m")

    # 3. Caractérisation de la zone
    _print_section("3. fr-characterize-zone — Population et vulnérabilités")
    char = _load_module("fr-characterize-zone", "characterize.py")
    commune = _safe("commune_info", char.commune_info, citycode)
    if commune:
        print(f"  Commune    : {commune['nom']} ({commune['code']})")
        print(f"  Population : {commune['population']:,} hab.".replace(",", " "))
        print(f"  Surface    : {commune['surface_km2']} km²  —  Densité : {commune['densite_hab_km2']} hab/km²")
    sens = _safe("sensitive_facilities", char.sensitive_facilities, lat, lon, radius=2000)
    if sens:
        print(f"  Équipements sensibles dans 2 km : {sens['counts']}")
        print(f"  Score vulnérabilité (pondéré)   : {sens['vulnerability_score']}")

    # 4. Accès à l'eau
    _print_section("4. fr-water-access — Eau (OSM + Hub'Eau)")
    water = _load_module("fr-water-access", "water_access.py")
    osm_water = _safe("osm_water", water.osm_water, lat, lon, radius=1500)
    if osm_water:
        print(f"  Points d'eau OSM dans 1,5 km : {osm_water['counts']}")
    quality = _safe("water_quality", water.water_quality, citycode, limit=5)
    if quality:
        print(f"  Qualité eau potable ({quality['sample_count']} prélèvements récents) :")
        print(f"    Dernier prélèvement     : {quality['latest_sample_date']}")
        print(f"    Non-conformités         : {quality['non_conformities']}")

    # 5. Météo
    _print_section("5. fr-weather-alerts — Conditions et alertes")
    weather = _load_module("fr-weather-alerts", "weather_alerts.py")
    wx = _safe("fr-weather-alerts", weather.build_report, lat, lon, days=3)
    if wx:
        cur = wx["current"]
        print(f"  Maintenant : {cur['temperature_2m']}°C, vent {cur['wind_speed_10m']} km/h, rafales {cur['wind_gusts_10m']} km/h")
        print(f"  Alertes par paramètre :")
        for k, v in wx["alerts"].items():
            print(f"    - {k:6s} : {v['level']:6s}  (jour={v['day']})")
        print(f"  NIVEAU GLOBAL : {wx['overall_level'].upper()}")

    # 6. Sanitaire
    _print_section("6. fr-health-alerts — Air et pollens")
    health = _load_module("fr-health-alerts", "health_alerts.py")
    h = _safe("fr-health-alerts", health.build_report, lat, lon)
    if h:
        print(f"  AQI européen : {h['air_quality']['european_aqi']} ({h['air_quality']['level']})")
        print(f"  PM2.5 : {h['air_quality']['pollutants']['pm2_5_ug_m3']} µg/m³")
        print(f"  PM10  : {h['air_quality']['pollutants']['pm10_ug_m3']} µg/m³")
        print(f"  Pollen dominant : {h['pollen']['dominant']} ({h['pollen']['level']})")
        print(f"  NIVEAU GLOBAL   : {h['overall_level'].upper()}")

    # 7. Profil de risque (Géorisques)
    _print_section("7. fr-georisques — Profil de risque historique")
    georisques = _load_module("fr-georisques", "georisques.py")
    risks = _safe("fr-georisques", georisques.build_report, citycode, 5, 3)
    if risks:
        recenses = risks.get("risques_recenses", [])
        print(f"  Risques recensés : {len(recenses)} types")
        top_categories = [r["label"] for r in recenses[:5]]
        for label in top_categories:
            print(f"    - {label}")
        catnat = risks.get("catnat", {})
        print(f"  Arrêtés CatNat (historique) : {catnat.get('total', 0)}")
        icpe = risks.get("icpe", {})
        print(f"  Installations classées (ICPE) : {icpe.get('total', 0)}")
        radon = risks.get("radon", {})
        print(f"  Radon : classe {radon.get('classe_potentiel')} ({radon.get('label')})")
        dicrim = risks.get("dicrim", {})
        print(f"  DICRIM publié : {dicrim.get('publie')} (année {dicrim.get('annee_publication') or '—'})")

    # 8. Cours d'eau (Vigicrues / Hub'Eau)
    _print_section("8. fr-vigicrues — Niveaux des cours d'eau temps réel")
    vigicrues = _load_module("fr-vigicrues", "vigicrues.py")
    crues = _safe("fr-vigicrues", vigicrues.build_report, lat, lon, 15, 5)
    if crues:
        stations = crues.get("stations", [])
        if stations:
            for s in stations[:3]:
                h_m = s.get("latest_height_m")
                trend = s.get("trend_24h", "—")
                delta = s.get("delta_24h_m")
                delta_s = f" ({delta:+.2f} m)" if delta is not None else ""
                h_s = f"{h_m} m" if h_m is not None else "—"
                print(f"    - {s.get('libelle', '—'):60s}  {h_s:>10s}  tendance: {trend}{delta_s}")
        else:
            print("    Aucune station de mesure dans le rayon analysé.")

    # 9. Surveillance épidémiologique (Sentinelles)
    _print_section("9. fr-sentinelles — Surveillance épidémiologique nationale")
    sentinelles = _load_module("fr-sentinelles", "sentinelles.py")
    epidemio = _safe("fr-sentinelles", sentinelles.build_report, "national", None, ["1", "3", "7"])
    if epidemio:
        if epidemio.get("week_iso"):
            print(f"  Semaine ISO : {epidemio['week_iso']}")
        for ind in epidemio.get("indicators", []):
            if "error" in ind:
                print(f"    - {ind.get('label', '—'):28s}  ERREUR ({ind['error']})")
                continue
            inc100 = ind.get("inc100")
            inc100_s = f"{inc100} /100k" if inc100 is not None else "—"
            print(f"    - {ind.get('label', '—'):28s}  {inc100_s:>12s}  niveau: {ind.get('level', '—')}")
        print(f"  NIVEAU GLOBAL : {epidemio.get('overall_level', '—').upper()}")

    # 10. Itinéraires vers les 3 hôpitaux les plus proches
    _print_section("10. fr-route — Itinéraires vers les 3 hôpitaux les plus proches")
    route = _load_module("fr-route", "route.py")
    hospitals = [x for x in (infra or {}).get("results", {}).get("health", []) if x["kind"] == "hospital"][:3]
    if hospitals:
        destinations = [{"lat": hp["lat"], "lon": hp["lon"], "label": hp["name"] or "(sans nom)"} for hp in hospitals]
        ranked = _safe("fr-route", route.osrm_routes, lat, lon, destinations)
        if ranked:
            for r in ranked["results"]:
                if "error" in r:
                    print(f"    - {r['label']:30s}  ERREUR ({r['error']})")
                else:
                    print(f"    - {r['label']:30s}  {r['distance_m']:>7.0f} m  /  {r['duration_human']}")
    else:
        print("    Aucun hôpital dans le rayon analysé (ou étape 2 indisponible).")

    # Synthèse
    _print_section("SYNTHÈSE")
    nearest_emergency = (infra or {}).get("results", {}).get("emergency", [None])[0] if infra else None
    nearest_hospital = next((x for x in (infra or {}).get("results", {}).get("health", []) if x["kind"] == "hospital"), None) if infra else None
    if commune:
        print(f"  Lieu             : {commune['nom']} — {commune['population']:,} hab.".replace(",", " "))
    if nearest_emergency:
        print(f"  Secours le + proche : {nearest_emergency['name']} à {nearest_emergency['distance_m']:.0f} m")
    if nearest_hospital:
        print(f"  Hôpital le + proche : {nearest_hospital['name']} à {nearest_hospital['distance_m']:.0f} m")
    if sens:
        print(f"  Vulnérabilité   : score {sens['vulnerability_score']} (EHPAD={sens['counts']['ehpad']}, écoles={sens['counts']['school']}, crèches={sens['counts']['kindergarten']})")
    if wx:
        print(f"  Météo           : {wx['overall_level']}")
    if h:
        print(f"  Sanitaire       : {h['overall_level']}")
    if risks:
        print(f"  Risques majeurs : {len(risks.get('risques_recenses', []))} recensés, {risks.get('catnat', {}).get('total', 0)} CatNat historiques")
    if crues and crues.get("stations"):
        rising = sum(1 for s in crues["stations"] if s.get("trend_24h") == "rising")
        if rising:
            print(f"  Hydrologie      : ⚠ {rising} station(s) en hausse sur 24 h")
        else:
            print(f"  Hydrologie      : {len(crues['stations'])} station(s) suivies, pas de hausse")
    if epidemio:
        print(f"  Épidémiologie   : {epidemio.get('overall_level', '—')}")
    print()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Démo d'orchestration des skills du plugin.")
    parser.add_argument(
        "--address",
        default="29 rue de Strasbourg, 44000 Nantes",
        help="Adresse de l'incident à analyser.",
    )
    args = parser.parse_args(argv)
    run_scenario(args.address)
    return 0


if __name__ == "__main__":
    sys.exit(main())
