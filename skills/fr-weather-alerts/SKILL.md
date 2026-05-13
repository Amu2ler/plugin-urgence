---
name: fr-weather-alerts
description: Récupère les prévisions météo et calcule un niveau d'alerte (vert/jaune/orange/rouge) pour un point en France à partir d'Open-Meteo (vent, pluie, neige, températures extrêmes). Renvoie aussi le lien vers la carte officielle Vigilance Météo-France. À DÉCLENCHER en cas de tempête, canicule, vague de froid, fortes pluies, ou pour planifier une opération sensible aux conditions météo.
---

# fr-weather-alerts — Alertes météo (Open-Meteo + Vigilance)

Combine deux sources :
- **Open-Meteo** (gratuit, sans clé) pour les prévisions horaires/journalières.
- Lien vers **Vigilance Météo-France** pour la carte officielle (l'API officielle nécessite une clé).

Le skill calcule un **niveau d'alerte par paramètre** (vent, pluie, neige, chaud, froid) en appliquant des seuils inspirés de la Vigilance Météo-France, puis un niveau global (le plus élevé).

## Quand utiliser ce skill

- "Quel temps prévu à [lieu] sur 3 jours ?"
- "Y a-t-il une alerte tempête / canicule / orage à venir ?"
- "Conditions pour une intervention extérieure ce week-end"

Pré-requis : **coordonnées GPS** → passe par `fr-geocode` si l'utilisateur donne une adresse.

## Utilisation

```bash
python skills/fr-weather-alerts/weather_alerts.py 47.218 -1.553 [--days 3]
```

## Format de sortie

```json
{
  "location": {"lat": 47.218, "lon": -1.553},
  "current": {
    "temperature_2m": 18.2,
    "wind_speed_10m": 22.5,
    "wind_gusts_10m": 41.8,
    "precipitation": 0.0,
    "weather_code": 3,
    "time": "2026-05-13T16:00"
  },
  "daily": [
    {
      "date": "2026-05-13",
      "tmin": 12, "tmax": 21,
      "precipitation_mm": 4.2,
      "wind_max_kmh": 28, "gust_max_kmh": 45,
      "weather_code": 61
    }
  ],
  "alerts": {
    "wind":  {"level": "green", "max_gust_kmh": 45, "day": "2026-05-13"},
    "rain":  {"level": "yellow", "max_mm": 65, "day": "2026-05-15"},
    "snow":  {"level": "green", "max_cm": 0, "day": null},
    "heat":  {"level": "green", "max_tmax": 22, "day": "2026-05-13"},
    "cold":  {"level": "green", "min_tmin": 8,  "day": "2026-05-14"}
  },
  "overall_level": "yellow",
  "vigilance_url": "https://vigilance.meteofrance.fr/"
}
```

## Seuils utilisés (inspirés de Vigilance Météo-France)

| Paramètre | Jaune | Orange | Rouge |
|---|---|---|---|
| Rafales (km/h) | ≥ 70 | ≥ 100 | ≥ 130 |
| Pluie 24 h (mm) | ≥ 30 | ≥ 50 | ≥ 100 |
| Neige 24 h (cm) | ≥ 3 | ≥ 10 | ≥ 20 |
| Tmax (°C) | ≥ 32 | ≥ 36 | ≥ 40 |
| Tmin (°C) | ≤ -5 | ≤ -10 | ≤ -15 |

Ces seuils sont approximatifs (pas modulés par département). Pour une décision opérationnelle réelle, consulter [vigilance.meteofrance.fr](https://vigilance.meteofrance.fr/).

## Bonnes pratiques

- Si `overall_level` ≥ `orange`, recommander de consulter la Vigilance officielle avant action.
- Le `weather_code` suit la norme WMO ; les codes 95-99 = orages.
- En cas d'alerte rouge ou orange, croiser avec `fr-characterize-zone` pour identifier les publics vulnérables exposés.
