---
description: Lance une analyse d'urgence complète sur une adresse française (situation, ressources, vulnérabilités, alertes).
argument-hint: <adresse en France>
---

# /urgence — Analyse d'urgence complète

Adresse à analyser : **$ARGUMENTS**

Lance une analyse multi-source en orchestrant les skills du plugin `plugin-urgence-fr`.

## Procédure à suivre

1. **Localiser** : exécute `fr-geocode` sur l'adresse pour obtenir `lat`, `lon`, et `citycode` (code INSEE).
   - Si le score de géocodage est inférieur à 0,5, signale l'ambiguïté à l'utilisateur avant de continuer.

2. **Identifier les ressources et risques opérationnels** :
   - `fr-locate-infra` (rayon 2000 m, types `health,emergency,shelter`) — hôpitaux, secours, lieux de repli.
   - `fr-water-access` (`all` avec `citycode`) — points d'eau, qualité eau potable.

3. **Caractériser le territoire** :
   - `fr-characterize-zone` (mode `full`) — population, densité, EHPAD, crèches, écoles, score de vulnérabilité.
   - `fr-georisques` (mode commune) — risques recensés, CatNat, ICPE, radon, DICRIM.

4. **Évaluer les alertes en temps réel** :
   - `fr-weather-alerts` (3 jours) — vent, pluie, neige, chaud, froid.
   - `fr-health-alerts` — qualité de l'air et pollens.
   - `fr-vigicrues` (rayon 15 km) — niveaux des cours d'eau et tendance 24h.

5. **Planifier l'évacuation / l'accès** :
   - `fr-route` (mode `routes`) — classer les 3 hôpitaux les plus proches par temps de trajet.

## Synthèse attendue

Produis une synthèse structurée en français comprenant :

- **Lieu** : commune, population, densité.
- **Profil de risque** : risques recensés (Géorisques) + score de vulnérabilité (équipements sensibles).
- **Situation actuelle** : niveau d'alerte météo / sanitaire / hydrologique (vert/jaune/orange/rouge).
- **Ressources accessibles** : 3 hôpitaux les plus proches avec temps de trajet, caserne(s) de pompiers, points d'eau.
- **Recommandations** : 3 à 5 actions prioritaires en fonction du contexte (publics vulnérables à informer, voies à privilégier, alertes officielles à consulter).

Si un skill renvoie une erreur, continue avec les autres et indique-le dans la synthèse. Cite les sources (BAN, OSM, Hub'Eau, Géorisques, Open-Meteo, OSRM) pour la transparence.
