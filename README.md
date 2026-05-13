# plugin-urgence-fr

Plugin Claude Code d'aide à la décision en situation d'urgence en France.

Il fournit un ensemble de **skills** que l'agent active à la demande pour répondre à trois besoins opérationnels :

1. **Localiser** un site, des routes, des accès à l'eau, des bâtiments.
2. **Caractériser** une zone (population, vulnérabilités, équipements sensibles).
3. **Surveiller** l'état d'alerte sanitaire, épidémiologique, météorologique.

## Skills inclus

| Skill | Rôle | Sources |
|---|---|---|
| `fr-geocode` | Adresse ↔ coordonnées, commune, code INSEE | BAN (api-adresse.data.gouv.fr) |
| `fr-locate-infra` | Routes, hôpitaux, écoles, casernes autour d'un point | Overpass / OpenStreetMap |
| `fr-water-access` | Points d'eau, qualité eau potable | Overpass + Hub'Eau |
| `fr-characterize-zone` | Population, équipements sensibles (EHPAD, écoles) | geo.api.gouv.fr + OSM |
| `fr-weather-alerts` | Vigilance Météo-France + prévisions | Vigilance + Open-Meteo |
| `fr-health-alerts` | Épidémies, qualité de l'air | Santé Publique France + Atmo |

## Installation

```bash
# Cloner le plugin
git clone https://github.com/Amu2ler/plugin-urgence.git

# Dans Claude Code, ajouter le plugin (à venir)
```

## Statut

Projet en cours de développement — voir les issues / commits pour l'avancement.

## Licence

MIT
