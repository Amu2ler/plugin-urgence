# Endpoints Géorisques utilisés

Base : `https://www.georisques.gouv.fr/api/v1/`

Doc officielle : <https://www.georisques.gouv.fr/doc-api>

Aucune clé API requise (API publique, anonyme).

## Les 5 endpoints interrogés par le skill

### 1. `/gaspar/risques?code_insee=<INSEE>&page_size=5`
Liste des risques recensés pour la commune (table GASPAR maintenue par la DGPR).
- Retour : structure paginée, `data[0].risques_detail[]`.
- Chaque détail : `num_risque` (code GASPAR) + `libelle_risque_long`.

### 2. `/gaspar/catnat?code_insee=<INSEE>&page_size=<N>`
Arrêtés de catastrophe naturelle publiés au JO pour la commune.
- Champs principaux : `date_debut_evt`, `date_fin_evt`, `libelle_risque_jo`, `code_national_catnat`.
- `data.total` (via `results`) donne le nombre total d'arrêtés.

### 3. `/installations_classees?code_insee=<INSEE>&page_size=<N>`
Installations classées pour la protection de l'environnement (ICPE).
- Champs : `raisonSociale`, `commune`, `codePostal`, `codeInsee`, `codeNaf`, `latitude`, `longitude`, et flags `bovins`, `porcs`, `volailles`, `carriere`, `eolienne`, `industrie`.
- ⚠ Le `codeInsee` peut référer à l'INSEE de l'exploitant (siège social), pas du site exploité.

### 4. `/radon?code_insee=<INSEE>`
Potentiel d'exposition radon de la commune.
- Renvoie `classe_potentiel` ∈ {1, 2, 3}.
- 1 = faible, 2 = moyen, 3 = significatif.

### 5. `/gaspar/dicrim?code_insee=<INSEE>`
Document d'Information Communal sur les Risques Majeurs.
- Présence + `annee_publication` si publié.

## Codes d'erreur observés

| Code | Cas | Action |
|---|---|---|
| 200 | OK | parser `data` |
| 404 | code INSEE inconnu | retourner objet vide |
| 429 | rate-limited | backoff + retry |
| 5xx | indispo serveur | log + continuer les autres endpoints |

Le script `georisques.py` enveloppe chaque endpoint dans `_safe()` pour que l'échec d'un endpoint n'interrompe pas les autres.

## Performance

Le skill fait **5 appels HTTP séquentiels** par commune. Temps total observé : 1–3 s avec une connexion correcte.
Pas de parallélisation pour rester respectueux de l'API publique.
