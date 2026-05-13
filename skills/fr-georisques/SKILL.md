---
name: fr-georisques
description: Agrège les risques connus d'une commune française via l'API Géorisques (BRGM) — inondations, mouvements de terrain, séismes, sites industriels classés (ICPE / Seveso), historique des arrêtés de catastrophe naturelle (CatNat), potentiel radon, existence d'un DICRIM. À DÉCLENCHER pour qualifier le profil de risque d'un lieu, identifier les antécédents d'un territoire, ou compléter une analyse d'urgence avec le contexte "risques majeurs".
---

# fr-georisques — Risques majeurs d'une commune (BRGM)

Interroge l'**API Géorisques** (gouvernementale, BRGM) pour récupérer en une seule commande :

- **Risques recensés** (inondation, séisme, mouvement de terrain, transport de matières dangereuses, industriel…)
- **Historique CatNat** : arrêtés de catastrophe naturelle publiés au JO
- **ICPE** : installations classées pour la protection de l'environnement (dont Seveso)
- **Radon** : potentiel d'exposition au radon (classes 1 à 3)
- **DICRIM** : présence d'un Document d'Information Communal sur les Risques Majeurs

## Quand utiliser ce skill

- "Quels risques majeurs sont recensés à [commune] ?"
- "Y a-t-il des sites Seveso autour de [lieu] ?"
- "Cette commune a-t-elle été déclarée en catastrophe naturelle récemment ?"
- En complément du skill `fr-characterize-zone` pour qualifier la vulnérabilité d'un territoire.

Pré-requis : **code INSEE** (champ `citycode` du skill `fr-geocode`).

## Utilisation

```bash
# Synthèse complète pour une commune
python skills/fr-georisques/georisques.py 44109

# Limiter le nombre d'arrêtés et d'ICPE listés
python skills/fr-georisques/georisques.py 44109 --catnat-limit 5 --icpe-limit 10
```

## Format de sortie

```json
{
  "code_insee": "44109",
  "commune": "Nantes",
  "risques_recenses": [
    {"num": "11",  "label": "Inondation"},
    {"num": "12",  "label": "Mouvement de terrain"},
    {"num": "13",  "label": "Séisme"},
    ...
  ],
  "catnat": {
    "total": 17,
    "recent": [
      {"date_debut": "09/07/2017", "libelle": "Inondations et/ou Coulées de Boue"},
      ...
    ]
  },
  "icpe": {
    "total": 150,
    "exemples": [
      {"raison_sociale": "...", "commune": "...", "lat": ..., "lon": ...}
    ]
  },
  "radon": {
    "classe_potentiel": 3,
    "label": "Significatif"
  },
  "dicrim": {
    "publie": true,
    "annee_publication": "2010"
  }
}
```

## Lecture des résultats

- **Risques recensés** : liste GASPAR officielle. Un grand nombre indique un territoire historiquement exposé.
- **CatNat** : la fréquence et le type d'arrêtés permettent de qualifier la récurrence (ex : 5 arrêtés inondation = territoire récurrent).
- **ICPE** : 150 sites pour Nantes = territoire industriel dense ; à croiser avec une recherche Seveso si l'incident concerne un risque chimique.
- **Radon** : classe 1 (faible) → 3 (significatif). Classe 3 = enjeu sanitaire long terme.
- **DICRIM** : sa présence indique une commune ayant déjà documenté ses risques pour ses habitants.

## Bonnes pratiques

- À utiliser en *contexte* d'analyse (préparation, planification, retour d'expérience), pas pour de la décision opérationnelle minute par minute (préférer Vigilance + Vigicrues).
- Les données ICPE sont parfois imparfaites (siège social ≠ lieu d'exploitation). Pour une décision réelle, recouper avec la fiche AIDA / Géorisques web.
- Pour une caractérisation complète d'urgence : combiner avec `fr-characterize-zone` (population & vulnérabilités) et `fr-weather-alerts` (conditions présentes).
