# plugin-urgence-fr

**Plugin Claude Code d'aide à la décision en situation d'urgence en France.**

L'agent dispose de 6 skills qu'il active à la demande pour répondre à trois besoins opérationnels :

1. **Localiser** un site, des routes, des accès à l'eau, des bâtiments.
2. **Caractériser** une zone (population, vulnérabilités, équipements sensibles).
3. **Surveiller** l'état d'alerte sanitaire, épidémiologique, météorologique.

Les skills sont composables : ils s'appellent les uns les autres (via leurs sorties JSON) pour répondre à des questions complexes (ex : "que se passe-t-il si une tempête frappe Nantes demain ?").

## Skills

| Skill | Rôle | Sources |
|---|---|---|
| [`fr-geocode`](skills/fr-geocode/SKILL.md) | Adresse ↔ coordonnées, commune, code INSEE | [BAN](https://adresse.data.gouv.fr/) |
| [`fr-locate-infra`](skills/fr-locate-infra/SKILL.md) | Hôpitaux, écoles, casernes, routes autour d'un point | [Overpass](https://overpass-api.de) / OpenStreetMap |
| [`fr-water-access`](skills/fr-water-access/SKILL.md) | Points d'eau OSM + qualité eau potable communale | Overpass + [Hub'Eau](https://hubeau.eaufrance.fr) |
| [`fr-characterize-zone`](skills/fr-characterize-zone/SKILL.md) | Population, densité, équipements sensibles (EHPAD, écoles) | [geo.api.gouv.fr](https://geo.api.gouv.fr) + Overpass |
| [`fr-weather-alerts`](skills/fr-weather-alerts/SKILL.md) | Prévisions + niveau d'alerte vent/pluie/neige/chaud/froid | [Open-Meteo](https://open-meteo.com) + [Vigilance MF](https://vigilance.meteofrance.fr) |
| [`fr-health-alerts`](skills/fr-health-alerts/SKILL.md) | AQI européen, polluants, 6 pollens | [Open-Meteo Air Quality](https://open-meteo.com/en/docs/air-quality-api) |

Toutes les sources sont **publiques et gratuites**, sans clé API requise.

## Installation dans Claude Code

```bash
# 1. Cloner le plugin localement
git clone https://github.com/Amu2ler/plugin-urgence.git

# 2. Dans Claude Code, ajouter le plugin (commande /plugin)
# OU ajouter le repo dans ~/.claude/settings.json sous "plugins"
```

Voir la [documentation Claude Code – plugins](https://docs.claude.com/en/docs/claude-code/plugins) pour les détails d'installation.

## Prérequis

- **Python 3.10+** (utilise uniquement la stdlib, pas de `pip install` nécessaire).
- Connexion Internet sortante (HTTPS) vers :
  - `api-adresse.data.gouv.fr`
  - `overpass-api.de`
  - `geo.api.gouv.fr`
  - `hubeau.eaufrance.fr`
  - `api.open-meteo.com`
  - `air-quality-api.open-meteo.com`

## Exemples d'utilisation (en CLI direct)

```bash
# Géocoder une adresse
python skills/fr-geocode/geocode.py forward "29 rue de Strasbourg, 44000 Nantes"

# Hôpitaux et casernes dans 2 km autour d'un point
python skills/fr-locate-infra/locate_infra.py 47.218 -1.553 --radius 2000 --types health,emergency

# Démographie de la commune
python skills/fr-characterize-zone/characterize.py commune 44109

# Alerte météo sur 3 jours
python skills/fr-weather-alerts/weather_alerts.py 47.218 -1.553 --days 3

# Qualité de l'air et pollens
python skills/fr-health-alerts/health_alerts.py 47.218 -1.553
```

## Scénario type (orchestration par l'agent)

> **Utilisateur** : "On signale un incendie au 29 rue de Strasbourg à Nantes. Donne-moi le contexte."

L'agent enchaîne :

1. `fr-geocode` → `lat=47.2187, lon=-1.5537, citycode=44109`
2. `fr-locate-infra` autour (2 km, `health,emergency`) → 5 hôpitaux/cliniques, caserne SDIS 44 à 670 m
3. `fr-characterize-zone` (commune 44109 + sensibles 2 km) → 327k habitants ; 6 EHPAD, 26 crèches, 56 écoles à proximité — score vulnérabilité 162
4. `fr-water-access` (OSM + Hub'Eau 44109) → 19 fontaines / canal Saint-Félix / Erdre à 715 m ; eau distribuée conforme
5. `fr-weather-alerts` → rafales 58 km/h (jaune) : aggravation possible si vent tourne
6. `fr-health-alerts` → AQI 38 (green) ; surveiller PM2.5 si feu intense

L'agent synthétise et propose une décision (évacuation EHPAD le plus proche, ressources hydrauliques à 700 m, etc.).

## Architecture

```
plugin-urgence-fr/
├── .claude-plugin/
│   └── plugin.json          # Manifest du plugin
├── skills/
│   ├── fr-geocode/
│   │   ├── SKILL.md         # Instructions pour l'agent
│   │   └── geocode.py       # Script CLI (sortie JSON)
│   ├── fr-locate-infra/
│   ├── fr-water-access/
│   ├── fr-characterize-zone/
│   ├── fr-weather-alerts/
│   └── fr-health-alerts/
└── README.md
```

Chaque skill est **autonome** : un dossier, un `SKILL.md` (frontmatter `name` + `description` qui déclenche l'activation par l'agent), un script Python qui imprime du JSON. Pas de dépendance entre dossiers ; pas de bibliothèque tierce.

## Licence

MIT
