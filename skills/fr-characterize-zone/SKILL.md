---
name: fr-characterize-zone
description: Caractérise une zone en France — population, superficie, densité (geo.api.gouv.fr / INSEE) et équipements sensibles à proximité (EHPAD, crèches, écoles, hôpitaux) via OpenStreetMap. Calcule un score de vulnérabilité pondéré. Trigger when user asks "combien d'habitants à [commune]", "population de", "publics vulnérables dans [zone]", "EHPAD près de", "personnes à évacuer", "densité", "caractériser une zone". Mots-clés : INSEE, population, densité, EHPAD, crèche, école, vulnérabilité, démographie.
allowed-tools: Bash(python *), Bash(python3 *)
---

# fr-characterize-zone — Caractérisation de zone

Fournit deux types d'information complémentaires :

1. **Démographie** d'une commune (geo.api.gouv.fr → INSEE) : nom, population, superficie, densité.
2. **Équipements sensibles** dans un rayon (Overpass / OSM) : EHPAD / maisons de retraite, crèches, écoles, hôpitaux, maternités.

## Quand utiliser ce skill

- "Combien d'habitants à [commune] ?"
- "Quels publics vulnérables dans la zone d'évacuation ?"
- "Y a-t-il des EHPAD à proximité du sinistre ?"
- Pour cadrer un ordre de grandeur des personnes potentiellement impactées.

Pré-requis :
- **Code INSEE** (champ `citycode` de `fr-geocode`) pour la population.
- **Coordonnées GPS + rayon** pour les équipements sensibles.

## Utilisation

```bash
# Démographie seule
python skills/fr-characterize-zone/characterize.py commune 44109

# Équipements sensibles autour d'un point
python skills/fr-characterize-zone/characterize.py sensitive 47.218 -1.553 --radius 2000

# Combiné
python skills/fr-characterize-zone/characterize.py full 44109 47.218 -1.553 --radius 2000
```

## Format de sortie

**commune** :
```json
{
  "code": "44109",
  "nom": "Nantes",
  "population": 320732,
  "surface_km2": 65.19,
  "densite_hab_km2": 4919.8,
  "codes_postaux": ["44000", "44100", "44200", "44300"]
}
```

**sensitive** :
```json
{
  "center": {"lat": 47.218, "lon": -1.553},
  "radius_m": 2000,
  "results": {
    "ehpad": [...],
    "school": [...],
    "kindergarten": [...],
    "hospital": [...]
  },
  "counts": {"ehpad": 4, "school": 12, ...},
  "vulnerability_score": 18
}
```

Le `vulnerability_score` est un indicateur synthétique pondéré :
- EHPAD : ×3 (occupants à mobilité réduite)
- Crèche : ×3 (enfants en bas âge)
- Hôpital / maternité : ×2 (publics déjà fragiles)
- École : ×1

Ce score est indicatif, à utiliser comme un signal de priorisation, pas comme une mesure réglementaire.

## Bonnes pratiques

- La donnée OSM "EHPAD" est sous-renseignée : croiser avec FINESS pour de la planification réelle.
- Pour les communes très étendues (ex. communes rurales), la population seule cache la dispersion réelle.
