---
description: Lance une analyse d'urgence complète sur une adresse française (situation, ressources, vulnérabilités, alertes).
argument-hint: <adresse en France>
---

# /urgence — Analyse d'urgence complète

Adresse à analyser : **$ARGUMENTS**

Lance une analyse multi-source en orchestrant les skills du plugin `plugin-urgence-fr`.

## ⚠️ Important — signatures CLI exactes

**N'INVENTE PAS les arguments des scripts.** Chaque script utilise des **sous-commandes positionnelles**, pas des `--flag`. Les commandes ci-dessous sont les signatures **exactes**, copie-les et remplace seulement les placeholders `<LAT>`, `<LON>`, `<CITYCODE>` (et `<ADRESSE>` pour le rapport HTML).

Sur Windows, utilise `python`. Sur Mac/Linux, si `python` n'existe pas, utilise `python3` (les deux sont autorisés par `allowed-tools`).

## Procédure

### Étape 1 — Géocodage

```bash
python skills/fr-geocode/geocode.py forward "<ADRESSE_ORIGINALE>"
```

Récupère `lat`, `lon`, `citycode` du premier résultat. Si `score < 0.5`, signale l'ambiguïté avant de continuer.

### Étape 2 — Analyses en parallèle

Lance ces 8 commandes (dans l'ordre, en parallèle si tu peux). Substitue `<LAT>`, `<LON>`, `<CITYCODE>` :

```bash
# Infrastructures critiques (hôpitaux, secours) — rayon 1500 m
python skills/fr-locate-infra/locate_infra.py <LAT> <LON> --radius 1500 --types health,emergency

# Eau (OSM points + Hub'Eau qualité)
python skills/fr-water-access/water_access.py all <LAT> <LON> <CITYCODE> --radius 1500

# Caractérisation : commune + équipements sensibles
python skills/fr-characterize-zone/characterize.py full <CITYCODE> <LAT> <LON> --radius 2000

# Risques majeurs Géorisques (citycode positionnel)
python skills/fr-georisques/georisques.py <CITYCODE>

# Météo + alertes (3 jours)
python skills/fr-weather-alerts/weather_alerts.py <LAT> <LON> --days 3

# Qualité air + pollens
python skills/fr-health-alerts/health_alerts.py <LAT> <LON>

# Niveaux des cours d'eau (rayon 15 km)
python skills/fr-vigicrues/vigicrues.py <LAT> <LON> --radius-km 15

# Épidémio Sentinelles — national (recommandé, sub-commande "national" sans argument)
python skills/fr-sentinelles/sentinelles.py national
```

**Attention** : ne mets PAS de `--flag` pour les sous-commandes (`all`, `full`, `national`, etc.). Ce sont des **positionnels**.

### Étape 3 — Itinéraires vers les 3 hôpitaux les plus proches

À partir du résultat de `fr-locate-infra` (catégorie `health`), extrais les 3 hôpitaux les plus proches avec leur lat/lon, puis :

```bash
python skills/fr-route/route.py routes <LAT> <LON> "<LAT_H1>,<LON_H1>,<NOM_H1>" "<LAT_H2>,<LON_H2>,<NOM_H2>" "<LAT_H3>,<LON_H3>,<NOM_H3>"
```

Le format de chaque destination est `lat,lon,label` (3 champs séparés par virgules, **pas** d'espace après la virgule à l'intérieur de la string).

### Étape 4 — Rapport HTML interactif

```bash
python report.py --address "<ADRESSE_ORIGINALE>" --output report.html
```

Une fois terminé, indique le chemin absolu du `report.html` et propose à l'utilisateur de l'ouvrir :
- Windows : `ii report.html` ou `start report.html`
- macOS : `open report.html`
- Linux : `xdg-open report.html`

## Synthèse à produire

Structure systématiquement en français :

1. **Lieu** : commune, population, densité.
2. **Profil de risque** : risques GASPAR recensés (Géorisques) + score de vulnérabilité (équipements sensibles).
3. **Situation actuelle** : niveau d'alerte météo / sanitaire / hydrologique / épidémio (vert/jaune/orange/rouge).
4. **Ressources accessibles** : 3 hôpitaux les plus proches avec temps de trajet, casernes, points d'eau.
5. **Recommandations** : 3 à 5 actions prioritaires.
6. **Rapport visuel** : chemin vers `report.html` + commande pour l'ouvrir.

## Si un skill échoue

Tous les scripts ont du retry interne (3 tentatives, backoff exponentiel). Si malgré ça un skill échoue :
- continue avec les autres
- indique-le clairement dans la synthèse, section "Données indisponibles"
- cite quand même les sources (BAN, OSM, Hub'Eau, Géorisques, Open-Meteo, OSRM, Sentiweb) pour la transparence
