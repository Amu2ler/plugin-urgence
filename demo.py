"""Script de démo : orchestration des 6 skills du plugin sur un scénario d'urgence.

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
    print("\nL'agent enchaîne les 6 skills du plugin pour construire le contexte.")

    # 1. Géocodage
    _print_section("1. fr-geocode — Localiser l'adresse")
    geocode = _load_module("fr-geocode", "geocode.py")
    g = geocode.forward(address, limit=1)
    if not g["results"]:
        print("Aucun résultat de géocodage. Abandon.")
        return
    loc = g["results"][0]
    lat, lon, citycode, label = loc["lat"], loc["lon"], loc["citycode"], loc["label"]
    print(f"  Adresse résolue : {label}")
    print(f"  Coordonnées     : {lat}, {lon}")
    print(f"  Code INSEE      : {citycode}  (score={loc['score']:.2f})")

    # 2. Infrastructures critiques
    _print_section("2. fr-locate-infra — Hôpitaux et secours dans 2 km")
    locate = _load_module("fr-locate-infra", "locate_infra.py")
    infra = locate.fetch_infrastructure(lat, lon, radius=2000, categories=["health", "emergency"])
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
    commune = char.commune_info(citycode)
    print(f"  Commune    : {commune['nom']} ({commune['code']})")
    print(f"  Population : {commune['population']:,} hab.".replace(",", " "))
    print(f"  Surface    : {commune['surface_km2']} km²  —  Densité : {commune['densite_hab_km2']} hab/km²")
    sens = char.sensitive_facilities(lat, lon, radius=2000)
    print(f"  Équipements sensibles dans 2 km : {sens['counts']}")
    print(f"  Score vulnérabilité (pondéré)   : {sens['vulnerability_score']}")

    # 4. Accès à l'eau
    _print_section("4. fr-water-access — Eau (OSM + Hub'Eau)")
    water = _load_module("fr-water-access", "water_access.py")
    osm_water = water.osm_water(lat, lon, radius=1500)
    print(f"  Points d'eau OSM dans 1,5 km : {osm_water['counts']}")
    quality = water.water_quality(citycode, limit=5)
    print(f"  Qualité eau potable ({quality['sample_count']} prélèvements récents) :")
    print(f"    Dernier prélèvement     : {quality['latest_sample_date']}")
    print(f"    Non-conformités         : {quality['non_conformities']}")

    # 5. Météo
    _print_section("5. fr-weather-alerts — Conditions et alertes")
    weather = _load_module("fr-weather-alerts", "weather_alerts.py")
    wx = weather.build_report(lat, lon, days=3)
    cur = wx["current"]
    print(f"  Maintenant : {cur['temperature_2m']}°C, vent {cur['wind_speed_10m']} km/h, rafales {cur['wind_gusts_10m']} km/h")
    print(f"  Alertes par paramètre :")
    for k, v in wx["alerts"].items():
        print(f"    - {k:6s} : {v['level']:6s}  (jour={v['day']})")
    print(f"  NIVEAU GLOBAL : {wx['overall_level'].upper()}")

    # 6. Sanitaire
    _print_section("6. fr-health-alerts — Air et pollens")
    health = _load_module("fr-health-alerts", "health_alerts.py")
    h = health.build_report(lat, lon)
    print(f"  AQI européen : {h['air_quality']['european_aqi']} ({h['air_quality']['level']})")
    print(f"  PM2.5 : {h['air_quality']['pollutants']['pm2_5_ug_m3']} µg/m³")
    print(f"  PM10  : {h['air_quality']['pollutants']['pm10_ug_m3']} µg/m³")
    print(f"  Pollen dominant : {h['pollen']['dominant']} ({h['pollen']['level']})")
    print(f"  NIVEAU GLOBAL   : {h['overall_level'].upper()}")

    # Synthèse
    _print_section("SYNTHÈSE")
    nearest_emergency = infra["results"]["emergency"][0] if infra["results"]["emergency"] else None
    nearest_hospital = next((x for x in infra["results"]["health"] if x["kind"] == "hospital"), None)
    print(f"  Lieu             : {commune['nom']} — {commune['population']:,} hab.".replace(",", " "))
    print(f"  Secours le + proche : {nearest_emergency['name'] if nearest_emergency else 'N/A'} à {nearest_emergency['distance_m']:.0f} m" if nearest_emergency else "  Aucun secours dans le rayon")
    if nearest_hospital:
        print(f"  Hôpital le + proche : {nearest_hospital['name']} à {nearest_hospital['distance_m']:.0f} m")
    print(f"  Vulnérabilité   : score {sens['vulnerability_score']} (EHPAD={sens['counts']['ehpad']}, écoles={sens['counts']['school']}, crèches={sens['counts']['kindergarten']})")
    print(f"  Météo           : {wx['overall_level']}")
    print(f"  Sanitaire       : {h['overall_level']}")
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
