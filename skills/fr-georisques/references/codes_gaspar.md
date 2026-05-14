# Table des codes GASPAR (risques recensés)

Les codes `num_risque` retournés par `/gaspar/risques` suivent la nomenclature **GASPAR** (Gestion ASsistée des Procédures Administratives relatives aux Risques) maintenue par la DGPR.

| Code | Libellé | Famille |
|---|---|---|
| 11 | Inondation | Inondation |
| 111 | Inondation par submersion marine | Inondation |
| 112 | Crue à débordement lent de cours d'eau | Inondation |
| 113 | Crue à débordement rapide de cours d'eau / crue torrentielle | Inondation |
| 114 | Ruissellement et coulée de boue | Inondation |
| 116 | Remontées de nappes naturelles | Inondation |
| 12 | Mouvement de terrain | Terre |
| 121 | Affaissements et effondrements d'origine anthropique (carrières) | Terre |
| 122 | Affaissements et effondrements d'origine naturelle (cavités) | Terre |
| 123 | Éboulement ou chutes de pierres et de blocs | Terre |
| 124 | Glissement de terrain | Terre |
| 125 | Avancée dunaire | Terre |
| 126 | Recul du trait de côte | Terre |
| 127 | Tassements différentiels (retrait-gonflement argiles) | Terre |
| 13 | Séisme | Terre |
| 14 | Volcanisme | Terre |
| 16 | Feu de forêt | Feu |
| 17 | Phénomène lié à l'atmosphère | Atmosphère |
| 172 | Tempête et grains (vent) | Atmosphère |
| 174 | Foudre | Atmosphère |
| 175 | Grêle | Atmosphère |
| 176 | Neige et pluies verglaçantes | Atmosphère |
| 18 | Radon | Sanitaire |
| 21 | Risque industriel | Industriel |
| 22 | Nucléaire | Industriel |
| 23 | Rupture de barrage | Industriel |
| 24 | Transport de marchandises dangereuses | Industriel |
| 25 | Engins de guerre | Historique |

## Interpréter les codes

- Codes à **2 chiffres** = grande famille (ex : 11 = Inondation).
- Codes à **3 chiffres** = sous-type précis (ex : 112 = crue lente).

Quand on présente la liste à l'utilisateur, il est plus parlant de regrouper par famille :
> "Nantes : inondation (4 sous-types), mouvement de terrain (7 sous-types), séisme, tempête, risque industriel, rupture de barrage, transport matières dangereuses, engins de guerre."

## Source officielle

Référentiel complet sur <https://www.georisques.gouv.fr/articles-risques>.
