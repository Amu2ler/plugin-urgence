---
name: fr-water-access
description: Trouve les ressources en eau autour d'un point en France — fontaines, châteaux d'eau, rivières, lacs (OpenStreetMap) — et la qualité de l'eau potable distribuée par commune (Hub'Eau qualité_eau_potable). Trigger when user asks "où trouver de l'eau potable", "points d'eau près de", "l'eau est-elle potable à [commune]", "qualité de l'eau", "fontaines", "rivières autour de", "coupure d'eau". Mots-clés : eau, eau potable, Hub'Eau, fontaine, château d'eau, rivière, qualité eau, ARS, drinking water.
allowed-tools: Bash(python *), Bash(python3 *)
---

# fr-water-access — Accès à l'eau (OSM + Hub'Eau)

Combine deux sources :
- **OpenStreetMap** (Overpass) pour les points d'eau physiques (fontaines, châteaux d'eau, surfaces d'eau).
- **Hub'Eau** (API publique du Système d'information sur l'eau) pour la qualité réglementaire de l'eau distribuée.

## Quand utiliser ce skill

- "Y a-t-il des points d'eau potable près de [lieu] ?"
- "L'eau du robinet est-elle conforme à [commune] ?"
- "Quelles rivières / lacs autour de la zone sinistrée ?"

Pré-requis :
- **Coordonnées GPS** pour les points d'eau OSM → passe par `fr-geocode` si l'utilisateur donne une adresse.
- **Code INSEE** pour la qualité d'eau (champ `citycode` du skill `fr-geocode`).

## Utilisation

```bash
# Points d'eau OSM dans un rayon de 1 km
python skills/fr-water-access/water_access.py osm 47.218 -1.553 --radius 1000

# Qualité eau potable récente pour la commune de Nantes (INSEE 44109)
python skills/fr-water-access/water_access.py quality 44109 --limit 20

# Combiné (les deux en une commande)
python skills/fr-water-access/water_access.py all 47.218 -1.553 44109 --radius 1500
```

## Format de sortie (osm)

```json
{
  "center": {"lat": 47.218, "lon": -1.553},
  "radius_m": 1000,
  "results": {
    "drinking_water": [
      {"name": "Fontaine", "lat": ..., "lon": ..., "distance_m": 234.0, "kind": "drinking_water"}
    ],
    "water_tower": [...],
    "surface_water": [...]
  },
  "counts": {...}
}
```

## Format de sortie (quality)

```json
{
  "citycode": "44109",
  "sample_count": 18,
  "latest_sample_date": "2024-12-10",
  "non_conformities": 1,
  "samples": [
    {
      "date_prelevement": "2024-12-10",
      "conclusion_conformite_prelevement": "C",
      "nom_uge": "...",
      "nom_distributeur": "..."
    }
  ]
}
```

`conclusion_conformite_prelevement` : phrase en français — "conforme aux exigences" ou "non conforme…". Le champ `non_conformities` agrège les prélèvements détectés comme non conformes.

## Bonnes pratiques

- Hub'Eau renvoie les prélèvements les plus récents en premier (`size=limit`).
- Si `non_conformities > 0`, alerter l'utilisateur et lister les paramètres en cause si possible.
- En zone rurale, monter le rayon OSM à 5000–10000 m.
