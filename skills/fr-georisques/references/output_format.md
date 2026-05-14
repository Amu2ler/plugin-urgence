# Format JSON détaillé renvoyé par `georisques.py`

Le script imprime un seul objet JSON sur stdout. Schéma :

```json
{
  "code_insee": "44109",
  "commune": "NANTES",
  "risques_recenses": [
    {"num": "11", "label": "Inondation"},
    {"num": "112", "label": "Par une crue à débordement lent de cours d'eau"}
  ],
  "catnat": {
    "total": 17,
    "recent": [
      {
        "date_debut": "07/10/2024",
        "date_fin": "12/10/2024",
        "libelle": "Inondations et/ou Coulées de Boue",
        "code_national": "INTE2501371A"
      }
    ]
  },
  "icpe": {
    "total": 150,
    "exemples": [
      {
        "raison_sociale": "...",
        "commune": "Nantes",
        "code_naf": "25",
        "lat": 47.198066,
        "lon": -1.599162,
        "elevage_bovins": false,
        "elevage_porcs": false,
        "elevage_volailles": false,
        "carriere": false,
        "eolienne": false,
        "industrie": true
      }
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

## Champs

| Champ | Type | Description |
|---|---|---|
| `code_insee` | string | Code INSEE communiqué en entrée |
| `commune` | string | Libellé de la commune (peut être absent si endpoint indispo) |
| `risques_recenses[]` | array | Liste GASPAR (code + libellé), cf. `codes_gaspar.md` |
| `catnat.total` | int | Nombre total d'arrêtés CatNat historiques |
| `catnat.recent[]` | array | N premiers arrêtés (par défaut 10) |
| `icpe.total` | int | Nombre d'ICPE rattachées à l'INSEE |
| `icpe.exemples[]` | array | Échantillon de N installations |
| `radon.classe_potentiel` | int | 1, 2 ou 3 |
| `radon.label` | string | "Faible", "Moyen", "Significatif" |
| `dicrim.publie` | bool | `true` si la commune a publié un DICRIM |
| `dicrim.annee_publication` | string | Année (si publié) |

## Robustesse aux échecs partiels

Le script utilise un `_safe(...)` wrapper. Si un endpoint échoue (404, 5xx, timeout), le champ correspondant est laissé à sa valeur par défaut et la clé `_error` peut apparaître pour ce sous-objet.

Exemple de sortie partielle :

```json
{
  "code_insee": "99999",
  "commune": null,
  "risques_recenses": [],
  "catnat": {"total": 0, "recent": []},
  "icpe": {"total": 0, "exemples": [], "_error": "HTTPError: 404", "_endpoint": "icpe"},
  ...
}
```
