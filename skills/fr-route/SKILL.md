---
name: fr-route
description: Calcule des itinéraires routiers (distance, durée, géométrie) entre deux points ou classe plusieurs destinations par temps de trajet en France via OSRM. Trigger when user asks "comment aller de A à B", "combien de temps pour aller à", "hôpital le plus rapide à atteindre", "trajet d'évacuation", "comparer les routes", "tournée de [sites]". Mots-clés : OSRM, itinéraire, route, trajet, évacuation, routing, time to reach, distance.
allowed-tools: Bash(python *), Bash(python3 *)
---

# fr-route — Itinéraires routiers (OSRM)

Calcule des itinéraires en utilisant **OSRM** (Open Source Routing Machine), avec le serveur public démo (`router.project-osrm.org`). Gratuit, sans clé.

Deux modes :

- **`route`** : itinéraire entre deux points (A → B).
- **`routes`** : un point de départ → plusieurs destinations, résultats triés par durée croissante. Idéal pour comparer plusieurs hôpitaux, EHPAD, ou zones de repli.

## Quand utiliser ce skill

- "Combien de temps pour aller de A à B ?"
- "Quel hôpital le plus rapide depuis le sinistre ?"
- "Itinéraire d'évacuation vers la mairie"
- "Comparer 3 zones de repli depuis le PC opérationnel"

Pré-requis : **coordonnées GPS** des points. Combiner avec :
- `fr-geocode` pour résoudre des adresses
- `fr-locate-infra` pour obtenir une liste de destinations candidates (hôpitaux, casernes, mairies)

## Utilisation

```bash
# Itinéraire simple A -> B
python skills/fr-route/route.py route 47.2187 -1.5537 47.2104 -1.5534

# Comparer plusieurs destinations depuis un point
python skills/fr-route/route.py routes 47.2187 -1.5537 \
  "47.2104,-1.5534,Hotel Dieu" \
  "47.2272,-1.5615,Clinique du Parc" \
  "47.2260,-1.5466,Clinique Bretéché"
```

## Format de sortie

**route** :
```json
{
  "from": {"lat": 47.2187, "lon": -1.5537},
  "to":   {"lat": 47.2104, "lon": -1.5534},
  "distance_m": 1240.5,
  "duration_s": 178.4,
  "duration_human": "3 min",
  "geometry": {"type": "LineString", "coordinates": [...]}
}
```

**routes** :
```json
{
  "from": {"lat": 47.2187, "lon": -1.5537},
  "results": [
    {
      "label": "Hotel Dieu",
      "to": {"lat": 47.2104, "lon": -1.5534},
      "distance_m": 1240.5,
      "duration_s": 178.4,
      "duration_human": "3 min"
    },
    {
      "label": "Clinique du Parc",
      ...
    }
  ]
}
```

Trié par `duration_s` croissante (le plus rapide en premier).

## Bonnes pratiques

- Le serveur public démo OSRM peut être lent ou avoir des coupures ; pour de la production, héberger sa propre instance.
- Profile par défaut : `driving`. Le démo public ne supporte pas `walking` / `cycling`.
- En zone bloquée (incendie, inondation), l'itinéraire ne tient pas compte des coupures en temps réel — à croiser avec d'autres signaux.
- Pour une évacuation de masse, OSRM ne prend pas en compte la capacité routière ; il donne le chemin le plus rapide à un instant t, à un véhicule seul.
