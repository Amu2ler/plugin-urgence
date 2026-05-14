# plugin-urgence-fr

**Plugin Claude Code d'aide à la décision en situation d'urgence en France.**

> Projet de groupe — IUT NFC, UMLP, 3ᵉ année (S6) — encadré par Christophe Guyeux.
> Auteurs : **Arthur Muller**, **Kylian Strub**, **Abdoulaye Diallo**.

Trois axes opérationnels :

1. **Localiser** un site, des routes, des accès à l'eau, des bâtiments.
2. **Caractériser** une zone (population, vulnérabilités, profil de risque historique).
3. **Surveiller** les alertes sanitaires, hydrologiques, météorologiques et épidémiologiques en temps réel.

Le plugin fournit **10 skills**, **1 slash command** `/urgence`, **1 sub-agent** `urgentiste`, un **script de démo console** et un **générateur de rapport HTML interactif** (carte Leaflet).

## Skills (10)

| Skill | Rôle | Sources |
|---|---|---|
| [`fr-geocode`](skills/fr-geocode/SKILL.md) | Adresse ↔ coordonnées, commune, code INSEE | [BAN](https://adresse.data.gouv.fr/) |
| [`fr-locate-infra`](skills/fr-locate-infra/SKILL.md) | Hôpitaux, écoles, casernes, routes autour d'un point | [Overpass](https://overpass-api.de) / OpenStreetMap |
| [`fr-water-access`](skills/fr-water-access/SKILL.md) | Points d'eau OSM + qualité eau potable communale | Overpass + [Hub'Eau](https://hubeau.eaufrance.fr) |
| [`fr-characterize-zone`](skills/fr-characterize-zone/SKILL.md) | Population, densité, EHPAD, crèches, écoles | [geo.api.gouv.fr](https://geo.api.gouv.fr) + Overpass |
| [`fr-georisques`](skills/fr-georisques/SKILL.md) | Profil de risque : ICPE, CatNat, radon, DICRIM | [Géorisques BRGM](https://www.georisques.gouv.fr) |
| [`fr-weather-alerts`](skills/fr-weather-alerts/SKILL.md) | Prévisions + niveau d'alerte vent/pluie/neige/chaud/froid | [Open-Meteo](https://open-meteo.com) + [Vigilance MF](https://vigilance.meteofrance.fr) |
| [`fr-health-alerts`](skills/fr-health-alerts/SKILL.md) | AQI européen, polluants, 6 pollens | [Open-Meteo Air Quality](https://open-meteo.com/en/docs/air-quality-api) |
| [`fr-vigicrues`](skills/fr-vigicrues/SKILL.md) | Niveaux d'eau temps réel + tendance 24 h | [Hub'Eau Hydrométrie](https://hubeau.eaufrance.fr) |
| [`fr-sentinelles`](skills/fr-sentinelles/SKILL.md) | Épidémiologie ville (grippe, gastro, varicelle) | [Réseau Sentinelles / Inserm](https://www.sentiweb.fr/) |
| [`fr-route`](skills/fr-route/SKILL.md) | Itinéraires routiers, classement de destinations | [OSRM](https://project-osrm.org/) |

Toutes les sources sont **publiques et gratuites**, sans clé API. **Zéro dépendance Python** (stdlib uniquement).

## Slash command et sub-agent

- **`/urgence <adresse>`** ([commands/urgence.md](commands/urgence.md)) — orchestre les 10 skills sur une adresse.
- **Sub-agent `urgentiste`** ([agents/urgentiste.md](agents/urgentiste.md)) — sait quand chaîner les skills, produit des synthèses opérationnelles structurées et sourcées.

## Conformité avec la méthodologie du cours

Le plugin respecte les bonnes pratiques exposées dans le brief `ProjetsSkills.pdf` :

- **Choix skills plutôt que MCPs** pour minimiser l'empreinte tokens en idle (~50 tokens par skill inactif).
- **Frontmatter** : chaque `SKILL.md` déclare `name`, `description` (Trigger when... + mots-clés FR/EN) et `allowed-tools` (défense en profondeur — `Bash(python *)` uniquement).
- **`references/`** : le skill `fr-georisques` démontre le levier "details à la demande" en externalisant `api.md`, `codes_gaspar.md`, `interpretation.md`, `output_format.md` chargés seulement quand l'agent en a besoin.
- **Logique en script CLI Python testable seul** : chaque `*.py` peut être lancé sans Claude.
- **Empreinte minimale** : pas de dépendance externe, scripts < 250 lignes, sorties JSON compactes.

## Installation dans Claude Code

```bash
git clone https://github.com/Amu2ler/plugin-urgence.git
```

Puis dans Claude Code : `/plugin` → ajouter le chemin local. Voir la [doc plugins](https://docs.claude.com/en/docs/claude-code/plugins).

## Prérequis

- **Python 3.10+** (stdlib uniquement, pas de `pip install`).
- Voir [`requirements.txt`](requirements.txt) et [`pyproject.toml`](pyproject.toml) pour les dépendances **optionnelles** (`pypdf`, `pyproj`, `pynsee`...).
- Connexion HTTPS vers les APIs publiques :
  - `api-adresse.data.gouv.fr` (BAN)
  - `overpass-api.de` (+ miroirs `kumi.systems`, `openstreetmap.fr`)
  - `geo.api.gouv.fr`
  - `hubeau.eaufrance.fr`
  - `www.georisques.gouv.fr`
  - `www.sentiweb.fr`
  - `api.open-meteo.com` + `air-quality-api.open-meteo.com`
  - `router.project-osrm.org`

## Démo console

```bash
python demo.py                                     # Nantes par défaut
python demo.py --address "1 rue de Rivoli, 75001 Paris"
```

## Rapport HTML interactif

```bash
python report.py                                   # produit report.html
python report.py --address "..." --output rapport.html
```

Ouvre le fichier dans un navigateur. La carte Leaflet affiche les hôpitaux, casernes, EHPAD, points d'eau, stations Vigicrues colorées selon la tendance, et les **3 itinéraires OSRM** vers les hôpitaux les plus rapides.

## Exemples d'utilisation CLI direct

```bash
python skills/fr-geocode/geocode.py forward "29 rue de Strasbourg, 44000 Nantes"
python skills/fr-locate-infra/locate_infra.py 47.218 -1.553 --radius 2000 --types health,emergency
python skills/fr-georisques/georisques.py 44109
python skills/fr-vigicrues/vigicrues.py 47.218 -1.553 --radius-km 15
python skills/fr-sentinelles/sentinelles.py national
python skills/fr-weather-alerts/weather_alerts.py 47.218 -1.553 --days 3
python skills/fr-health-alerts/health_alerts.py 47.218 -1.553
python skills/fr-route/route.py routes 47.2187 -1.5537 \
  "47.2104,-1.5534,Hotel Dieu" "47.2272,-1.5615,Clinique du Parc"
```

## Scénario type (orchestration par l'agent)

> **Utilisateur** : "On signale un incendie au 29 rue de Strasbourg à Nantes. Donne-moi le contexte."

L'agent enchaîne :

1. `fr-geocode` → `lat=47.2187, lon=-1.5537, citycode=44109`
2. `fr-locate-infra` → CHU + caserne SDIS à 680 m + commissariats
3. `fr-characterize-zone` → 327 k habitants ; 9 EHPAD, 42 crèches, 88 écoles — vulnérabilité 251
4. `fr-water-access` → 53 fontaines, Loire et Erdre à proximité, eau distribuée conforme
5. `fr-weather-alerts` → vent 28 km/h, rafales 54 km/h (alerte verte)
6. `fr-health-alerts` → AQI 38 (green), graminées 9.6 (yellow)
7. `fr-georisques` → 22 risques recensés, 17 CatNat historiques, radon classe 3
8. `fr-vigicrues` → la Loire à Sainte-Luce à 3.47 m, **en hausse de +50 cm sur 24 h**
9. `fr-sentinelles` → grippe + gastro + varicelle au niveau national (green)
10. `fr-route` → Hôtel Dieu accessible en 4 min, Le Tourville en 4 min

L'agent synthétise et recommande (mise en alerte des EHPAD à proximité, surveillance du niveau de la Loire, orientation des secours vers l'Hôtel Dieu).

## Architecture

```
plugin-urgence-fr/
├── .claude-plugin/
│   └── plugin.json
├── commands/
│   └── urgence.md
├── agents/
│   └── urgentiste.md
├── skills/                          # 10 skills, chacun autonome
│   ├── fr-geocode/
│   ├── fr-locate-infra/
│   ├── fr-water-access/
│   ├── fr-characterize-zone/
│   ├── fr-georisques/
│   │   ├── SKILL.md
│   │   ├── georisques.py
│   │   └── references/              # progressive disclosure
│   │       ├── api.md
│   │       ├── codes_gaspar.md
│   │       ├── interpretation.md
│   │       └── output_format.md
│   ├── fr-weather-alerts/
│   ├── fr-health-alerts/
│   ├── fr-vigicrues/
│   ├── fr-sentinelles/
│   └── fr-route/
├── demo.py                          # Démo console (10 skills enchaînés)
├── report.py                        # Génère report.html (carte + KPIs)
├── requirements.txt
├── pyproject.toml
└── README.md
```

## Livrable et rendu

Conformément au brief :
- Dépôt GitHub public : <https://github.com/Amu2ler/plugin-urgence>
- Groupe : Arthur Muller, Kylian Strub, Abdoulaye Diallo
- Échéance : **vendredi 12 juin 2026**, fin de journée

## Licence

MIT
