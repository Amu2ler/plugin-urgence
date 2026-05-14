---
name: fr-vigicrues
description: Donne les niveaux d'eau des cours d'eau (rivières, fleuves) en temps réel autour d'un point en France via Hub'Eau Hydrométrie, avec tendance sur 24 h (rising/falling/stable). Renvoie aussi le lien vers vigicrues.gouv.fr. Trigger when user asks "niveau de [rivière/fleuve]", "risque de crue", "débordement", "hydrologie", "Vigicrues", "la Loire monte", "inondation imminente". Mots-clés - Vigicrues, Hub'Eau, hydrométrie, crue, niveau d'eau, rivière, fleuve, inondation, flood.
allowed-tools: Bash(python *), Bash(python3 *)
---

# fr-vigicrues — Niveaux d'eau temps réel (Hub'Eau + Vigicrues)

Interroge **Hub'Eau Hydrométrie** (API officielle, gratuite, sans clé) pour obtenir :

- Les **stations de mesure** des cours d'eau dans un rayon autour d'un point.
- Le **niveau d'eau le plus récent** (hauteur en mètres) pour chaque station.
- La **tendance sur 24 h** (montée / descente / stable, avec delta en mètres).

Renvoie aussi le lien vers la **carte officielle Vigicrues** (jaune/orange/rouge par territoire) pour le contexte d'alerte.

## Quand utiliser ce skill

- "Quel niveau de la Loire à Nantes ?"
- "Y a-t-il un risque de crue dans les prochaines heures ?"
- "Les rivières montent-elles autour de [lieu] ?"
- En complément de `fr-weather-alerts` si pluie/orage annoncés en amont.

Pré-requis : **coordonnées GPS** → passe par `fr-geocode` si l'utilisateur donne une adresse.

## Utilisation

```bash
# Stations dans un rayon de 15 km
python skills/fr-vigicrues/vigicrues.py 47.218 -1.553 --radius-km 15

# Limiter le nombre de stations
python skills/fr-vigicrues/vigicrues.py 47.218 -1.553 --radius-km 20 --limit 5
```

## Format de sortie

```json
{
  "search": {"lat": 47.218, "lon": -1.553, "radius_km": 15},
  "stations_count": 6,
  "stations": [
    {
      "code_station": "M622001030",
      "libelle": "La Loire à Sainte-Luce-sur-Loire - Pont de Bellevue",
      "cours_eau": "la Loire",
      "commune": "SAINTE-LUCE-SUR-LOIRE",
      "lat": 47.229718,
      "lon": -1.468840,
      "distance_km": 6.5,
      "latest_height_m": 3.47,
      "latest_obs_date": "2026-05-12T06:00:00Z",
      "trend_24h": "rising",
      "delta_24h_m": 0.12
    }
  ],
  "vigicrues_url": "https://www.vigicrues.gouv.fr/"
}
```

- `latest_height_m` : hauteur d'eau (m) à la dernière observation.
- `trend_24h` : `rising` (delta > +5 cm), `falling` (delta < −5 cm), `stable` sinon.
- `delta_24h_m` : variation sur les ~24 dernières heures.

## Bonnes pratiques

- Une station qui monte rapidement (>30 cm en 24h) est un signal de crue en cours.
- Les seuils d'alerte officielle (jaune/orange/rouge) sont définis par station et publiés sur [vigicrues.gouv.fr](https://www.vigicrues.gouv.fr/) — toujours croiser avec.
- En cas de niveau anormal : croiser avec `fr-georisques` (risque inondation recensé) et `fr-characterize-zone` (vulnérabilités exposées).
- Le réseau de stations n'est pas exhaustif. Une absence de station ne signifie pas absence de cours d'eau.
