# Comment lire la sortie de `fr-georisques`

## Risques recensés

Une liste **longue** (> 15 codes) ne signifie pas qu'un risque est imminent : c'est l'inventaire des risques *connus et documentés* pour la commune. Une commune côtière aura nécessairement plusieurs codes inondation + recul du trait de côte. À interpréter comme un **profil**, pas comme une alerte.

Pour qualifier l'urgence présente, croiser avec :
- `fr-weather-alerts` (météo en cours)
- `fr-vigicrues` (niveaux de cours d'eau temps réel)

## CatNat (arrêtés de catastrophe naturelle)

- Un `catnat.total` élevé indique une commune historiquement exposée.
- La **récurrence** (plusieurs arrêtés inondation en 10 ans) est un signal fort de territoire à risque.
- Croiser les dates avec l'événement en cours : si la commune a déjà été déclarée en catastrophe en 2024, le PPRI est probablement à jour.

## ICPE

- Le champ `total` peut être trompeur :
  - Inclut **tous les régimes** (déclaration, enregistrement, autorisation).
  - Le champ `codeInsee` réfère parfois au **siège social** de l'exploitant, pas au site exploité.
- Pour qualifier un risque industriel proche d'un incident, croiser avec `fr-locate-infra` (positions OSM) ou une requête géographique sur la fiche AIDA.

## Radon

| Classe | Lecture |
|---|---|
| 1 | Potentiel faible. Pas d'enjeu particulier au-delà de l'aération courante. |
| 2 | Potentiel moyen. Le bâti récent est en général conforme ; surveiller les sous-sols. |
| 3 | Potentiel significatif. Le diagnostic est recommandé dans le bâti recevant du public. |

Le radon est un **risque chronique** (cancer du poumon lié à l'exposition long terme), pas un signal d'urgence. À mentionner uniquement si la question porte sur la santé environnementale, pas dans une analyse d'urgence aiguë.

## DICRIM

La présence d'un DICRIM (Document d'Information Communal sur les Risques Majeurs) indique que la commune a déjà communiqué publiquement sur ses risques. Son absence n'est pas une infraction — beaucoup de communes en sont dépourvues, surtout les plus petites.

## Limites des données Géorisques

- Fraîcheur : les données GASPAR sont mises à jour annuellement, pas en temps réel.
- Exhaustivité : tous les sites industriels ne sont pas géoréférencés finement.
- Pour une décision opérationnelle réelle (intervention pompiers, évacuation), recouper avec les sources locales (préfecture, SDIS, AIDA).
