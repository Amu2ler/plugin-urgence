---
name: fr-locate-infra
description: Localise les infrastructures critiques (hôpitaux, cliniques, pharmacies, écoles, casernes de pompiers, police, gendarmeries, gares, aérodromes, axes routiers) autour d'un point en France via OpenStreetMap / Overpass. Trigger when user asks "qu'est-ce qu'il y a autour de", "hôpitaux les plus proches", "casernes proches", "axes routiers près de", "planifier une évacuation", "infrastructures proches de [lieu]". Mots-clés - OSM, Overpass, hôpital, pompiers, police, école, infrastructure, équipement, autour de, à proximité.
allowed-tools: Bash(python *), Bash(python3 *)
---

# fr-locate-infra — Infrastructures critiques (Overpass / OSM)

Récupère, dans un rayon autour d'un point, les infrastructures utiles en situation d'urgence à partir d'**OpenStreetMap** via l'API publique Overpass.

## Quand utiliser ce skill

- "Quels hôpitaux à moins de 5 km de [adresse] ?"
- "Casernes de pompiers autour du sinistre"
- "Routes principales pour évacuer [zone]"
- "Y a-t-il une gare, un aérodrome proche ?"

Pré-requis : **coordonnées GPS**. Si l'utilisateur donne une adresse, lance d'abord le skill `fr-geocode`.

## Types disponibles

| Catégorie | Inclut |
|---|---|
| `health` | hôpitaux, cliniques, médecins, pharmacies |
| `emergency` | casernes de pompiers, police, gendarmerie |
| `education` | écoles, collèges, lycées, universités, crèches |
| `transport` | gares, stations de métro, aérodromes |
| `roads` | routes primaires/secondaires (highway=primary,secondary,trunk,motorway) |
| `shelter` | salles communales, mairies, gymnases |
| `all` | tous les précédents |

## Utilisation

```bash
# Tout dans un rayon de 2 km
python skills/fr-locate-infra/locate_infra.py 47.218 -1.553 --radius 2000 --types all

# Juste les hôpitaux et casernes, rayon 5 km
python skills/fr-locate-infra/locate_infra.py 47.218 -1.553 --radius 5000 --types health,emergency
```

## Format de sortie

JSON sur stdout :

```json
{
  "center": {"lat": 47.218, "lon": -1.553},
  "radius_m": 2000,
  "types": ["health", "emergency"],
  "results": {
    "health": [
      {
        "name": "CHU de Nantes",
        "lat": 47.219, "lon": -1.554,
        "distance_m": 412,
        "kind": "hospital",
        "tags": {"emergency": "yes", "phone": "+33..."}
      }
    ],
    "emergency": [ ... ]
  },
  "counts": {"health": 12, "emergency": 3}
}
```

Les résultats sont triés par distance croissante. La distance est calculée en formule de Haversine.

## Bonnes pratiques

- Rayon par défaut : 2000 m. Pour une zone rurale, monter à 10000–20000 m.
- Overpass peut être lent (5–15 s pour les grandes requêtes). Si timeout, réduire le rayon ou les types.
- Les données OSM ne sont pas exhaustives. Pour de la planification réelle, croiser avec d'autres sources.
