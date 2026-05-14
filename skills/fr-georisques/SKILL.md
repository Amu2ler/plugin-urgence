---
name: fr-georisques
description: Agrège les risques majeurs d'une commune française via l'API Géorisques (BRGM) — inondations, mouvements de terrain, séismes, sites industriels classés ICPE/Seveso, arrêtés de catastrophe naturelle CatNat, potentiel radon, DICRIM. Trigger when user asks "quels risques à [commune]", "y a-t-il des sites Seveso", "ICPE près de", "catastrophes naturelles historiques", "risques majeurs", "exposition radon", "DICRIM". Mots-clés - Géorisques, BRGM, ICPE, Seveso, CatNat, radon, DICRIM, risque majeur, inondation, séisme.
allowed-tools: Bash(python *), Bash(python3 *)
---

# fr-georisques — Risques majeurs d'une commune (BRGM)

Synthèse en une commande de 5 sources Géorisques pour un code INSEE :
risques recensés (GASPAR), CatNat, ICPE, radon, DICRIM.

## Utilisation

```bash
python skills/fr-georisques/georisques.py <citycode_INSEE> [--catnat-limit N] [--icpe-limit N]
```

Exemple : `python skills/fr-georisques/georisques.py 44109`

## Format de sortie

JSON sur stdout. Structure complète et détails de classification : voir [`references/output_format.md`](references/output_format.md).

Résumé :
- `risques_recenses` : liste des codes GASPAR (cf. [`references/codes_gaspar.md`](references/codes_gaspar.md))
- `catnat` : historique des arrêtés de catastrophe naturelle
- `icpe` : installations classées (échantillon)
- `radon` : classe 1 (faible), 2 (moyen), 3 (significatif)
- `dicrim` : présence d'un document d'information communal

## Quand utiliser ce skill

- "Quels risques recensés à [commune] ?"
- "Y a-t-il des sites Seveso à proximité ?"
- "Cette commune a-t-elle déjà été déclarée en catastrophe naturelle ?"
- Complète idéalement `fr-characterize-zone` pour qualifier le profil de risque d'un territoire.

## Bonnes pratiques de lecture

Pour interpréter correctement les résultats (codes radon, dates CatNat, distinction siège social vs site d'exploitation ICPE), consulter [`references/interpretation.md`](references/interpretation.md).

## Détail des endpoints API

Voir [`references/api.md`](references/api.md) pour la liste des 5 endpoints Géorisques utilisés, leurs paramètres et leurs codes de réponse.
