---
name: fr-health-alerts
description: Évalue les risques sanitaires environnementaux pour un point en France via Open-Meteo Air Quality — indice européen AQI, PM2.5, PM10, NO2, O3, SO2, CO, 6 pollens (graminées, bouleau, aulne, olivier, armoise, ambroisie). Trigger when user asks "qualité de l'air", "pollution à [lieu]", "pic de pollen", "smog", "PM2.5", "AQI", "alerte sanitaire", "consignes asthme/BPCO". Mots-clés - AQI, qualité air, pollution, Atmo, Géod'air, Santé Publique France, pollen, PM2.5, PM10, ozone, air quality.
allowed-tools: Bash(python *), Bash(python3 *)
---

# fr-health-alerts — Alertes sanitaires (air + pollens)

Récupère les indicateurs sanitaires environnementaux en temps réel via **Open-Meteo Air Quality** (gratuit, sans clé) :

- **Indice européen AQI** + concentrations PM2.5, PM10, NO2, O3, SO2, CO
- **Pollens** : graminées, bouleau, aulne, olivier, armoise, ambroisie

Niveau global (green / yellow / orange / red) calculé en prenant le pire des indicateurs.

> Pour le contexte épidémiologique (épidémies, alertes Santé Publique France), il n'existe pas d'API temps réel publique unifiée. Le skill renvoie les URLs de référence à consulter par l'utilisateur.

## Quand utiliser ce skill

- "Quelle qualité d'air à [lieu] ?"
- "Pic de pollution à venir ?"
- "Consignes pour personnes asthmatiques aujourd'hui ?"
- "Alerte pollen ?"

Pré-requis : **coordonnées GPS** → passe par `fr-geocode` si l'utilisateur donne une adresse.

## Utilisation

```bash
python skills/fr-health-alerts/health_alerts.py 47.218 -1.553
```

## Format de sortie

```json
{
  "location": {"lat": 47.218, "lon": -1.553},
  "air_quality": {
    "european_aqi": 35,
    "level": "yellow",
    "pollutants": {
      "pm2_5_ug_m3": 8.2,
      "pm10_ug_m3": 15.4,
      "nitrogen_dioxide_ug_m3": 22.1,
      "ozone_ug_m3": 78.3,
      "sulphur_dioxide_ug_m3": 1.5,
      "carbon_monoxide_ug_m3": 220
    }
  },
  "pollen": {
    "grass_grain_m3": 0,
    "birch_grain_m3": 12,
    "ragweed_grain_m3": 0,
    "olive_grain_m3": 0,
    "alder_grain_m3": 0,
    "mugwort_grain_m3": 0,
    "level": "yellow",
    "dominant": "birch"
  },
  "overall_level": "yellow",
  "references": {
    "sante_publique_france": "https://www.santepubliquefrance.fr/",
    "atmo_france": "https://www.atmo-france.org/",
    "pollens_rnsa": "https://www.pollens.fr/"
  }
}
```

## Seuils utilisés

**Indice européen AQI (`european_aqi`)** :
| AQI | Niveau |
|---|---|
| 0-40 | green |
| 40-60 | yellow |
| 60-80 | orange |
| ≥ 80 | red |

**Pollens (grains/m³, par type)** :
| Concentration | Niveau |
|---|---|
| < 5 | green |
| 5-30 | yellow |
| 30-100 | orange |
| ≥ 100 | red |

## Bonnes pratiques

- Niveau orange/rouge AQI → recommander aux publics fragiles (asthmatiques, BPCO, enfants, personnes âgées) de limiter les efforts en extérieur.
- Niveau orange/rouge pollen → croiser avec `fr-characterize-zone` pour cibler EHPAD/écoles à informer.
- Pour une décision médicale ou réglementaire, renvoyer vers Atmo France (organisme officiel agréé qualité de l'air) et Santé Publique France.
