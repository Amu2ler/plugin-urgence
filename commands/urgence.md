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
   - `fr-locate-infra` (rayon **1500 m**, types `health,emergency` — n'inclus PAS `shelter` qui surcharge Overpass) — hôpitaux, secours.
   - `fr-water-access` (`all` avec `citycode`) — points d'eau, qualité eau potable.
   - Note : sur Mac/Linux, si `python` n'est pas trouvé, retente immédiatement avec `python3` (les scripts sont compatibles avec les deux).

3. **Caractériser le territoire** :
   - `fr-characterize-zone` (mode `full`) — population, densité, EHPAD, crèches, écoles, score de vulnérabilité.
   - `fr-georisques` (mode commune) — risques recensés, CatNat, ICPE, radon, DICRIM.

4. **Évaluer les alertes en temps réel** :
   - `fr-weather-alerts` (3 jours) — vent, pluie, neige, chaud, froid.
   - `fr-health-alerts` — qualité de l'air et pollens.
   - `fr-vigicrues` (rayon 15 km) — niveaux des cours d'eau et tendance 24h.
   - `fr-sentinelles` — incidence grippe, gastro, varicelle (national, ou régional si tu connais le code région).

5. **Planifier l'évacuation / l'accès** :
   - `fr-route` (mode `routes`) — classer les 3 hôpitaux les plus proches par temps de trajet.

6. **Générer le rapport HTML interactif** (carte Leaflet + KPIs visuels) :
   - Exécute en arrière-plan : `python report.py --address "<adresse_originale_fournie_par_l_utilisateur>" --output report.html`
   - Une fois le script terminé, donne à l'utilisateur le **chemin absolu** du fichier `report.html` produit et propose-lui de l'ouvrir dans un navigateur (sur Windows : `ii report.html` ou `start report.html` ; sur macOS : `open report.html` ; sur Linux : `xdg-open report.html`).
   - Le rapport HTML est complémentaire de la synthèse texte : la synthèse résume oralement, le rapport visualise géographiquement (hôpitaux, EHPAD, points d'eau, itinéraires colorés, stations Vigicrues).

## Synthèse attendue

Produis une synthèse structurée en français comprenant :

- **Lieu** : commune, population, densité.
- **Profil de risque** : risques recensés (Géorisques) + score de vulnérabilité (équipements sensibles).
- **Situation actuelle** : niveau d'alerte météo / sanitaire / hydrologique (vert/jaune/orange/rouge).
- **Ressources accessibles** : 3 hôpitaux les plus proches avec temps de trajet, caserne(s) de pompiers, points d'eau.
- **Recommandations** : 3 à 5 actions prioritaires en fonction du contexte (publics vulnérables à informer, voies à privilégier, alertes officielles à consulter).
- **Rapport visuel** : indique le chemin vers `report.html` et la commande pour l'ouvrir.

Si un skill renvoie une erreur (timeout, rate-limit), continue avec les autres et indique-le dans la synthèse. Tous les scripts ont du retry interne (3 tentatives, backoff exponentiel), mais une coupure réseau persistante peut quand même faire échouer un skill — c'est attendu et géré gracieusement. Cite les sources (BAN, OSM, Hub'Eau, Géorisques, Open-Meteo, OSRM, Sentiweb) pour la transparence.
