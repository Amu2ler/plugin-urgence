---
name: fr-sentinelles
description: Récupère les indicateurs d'épidémiologie de ville en temps réel via le Réseau Sentinelles (Sentiweb / Inserm-Sorbonne) — syndromes grippaux, diarrhée aiguë, varicelle, etc. — au niveau national ou régional, avec niveau d'alerte (épidémie/pré-épidémie/normal). Trigger when user asks "épidémie en cours", "grippe à [lieu]", "gastro", "varicelle", "Sentinelles", "incidence", "épidémiologie ville". Mots-clés - Sentinelles, Sentiweb, Inserm, épidémio, grippe, gastro, IRA, varicelle, incidence, épidémie.
allowed-tools: Bash(python *), Bash(python3 *)
---

# fr-sentinelles — Surveillance épidémiologique (Réseau Sentinelles)

Interroge l'**API Sentiweb** (Réseau Sentinelles, Inserm / Sorbonne Université) qui publie chaque semaine l'incidence estimée de plusieurs pathologies de ville en France métropolitaine.

L'incidence est exprimée en :
- **cases / semaine** (`inc`)
- **cases / 100 000 habitants** (`inc100`) — plus parlant pour comparer.

## Quand utiliser ce skill

- "Y a-t-il une épidémie de grippe en cours ?"
- "Niveau de la gastro à [lieu] ?"
- "État de la surveillance varicelle ?"
- En complément de `fr-health-alerts` (qui gère l'air et les pollens, pas les épidémies).

Pas de pré-requis si on veut le national. Pour le régional : **code de région INSEE** (ex. 52 = Pays de la Loire, 11 = Île-de-France) — récupérable depuis `fr-geocode` puis `geo.api.gouv.fr`.

## Utilisation

```bash
# Indicateurs Sentinelles au niveau national (dernière semaine)
python skills/fr-sentinelles/sentinelles.py national

# À l'échelle d'une région (code INSEE de région)
python skills/fr-sentinelles/sentinelles.py region 52

# Choisir un indicateur précis
python skills/fr-sentinelles/sentinelles.py national --indicators 1,3
```

## Indicateurs suivis (par défaut)

| ID | Pathologie | Type |
|---|---|---|
| 1 | Syndromes grippaux | IRA |
| 3 | Diarrhée aiguë | digestive |
| 7 | Varicelle | éruptive |

D'autres IDs existent (cf. `references/indicators.md` si présent) et peuvent être passés via `--indicators`.

## Format de sortie

```json
{
  "geo_level": "PAY",
  "geo_filter": null,
  "week_iso": 202619,
  "indicators": [
    {
      "id": "1",
      "label": "Syndromes grippaux",
      "geo_insee": "FR",
      "geo_name": "France",
      "inc": 11600,
      "inc100": 17,
      "inc100_low": 10,
      "inc100_up": 24,
      "level": "green"
    }
  ],
  "overall_level": "green",
  "source": "https://www.sentiweb.fr/"
}
```

## Seuils d'alerte (heuristiques)

| `inc100` (cas / 100 000 hab.) | Niveau |
|---|---|
| < 50 | green |
| 50 – 100 | yellow |
| 100 – 200 | orange |
| ≥ 200 | red (épidémie active) |

Ces seuils sont approximatifs et ne remplacent pas la déclaration officielle d'épidémie par Santé Publique France. Pour le statut officiel, consulter le bulletin hebdomadaire du [Réseau Sentinelles](https://www.sentiweb.fr/).

## Bonnes pratiques

- En hiver, suivre l'indicateur 1 (grippe) hebdomadairement.
- En cas de pic gastro (3), recommander aux EHPAD / crèches d'isoler les cas (croiser avec `fr-characterize-zone`).
- Les codes région INSEE sont à 2 chiffres : `11` IDF, `24` Centre-Val de Loire, `27` Bourgogne-FC, `28` Normandie, `32` Hauts-de-France, `44` Grand Est, `52` Pays de la Loire, `53` Bretagne, `75` Nouvelle-Aquitaine, `76` Occitanie, `84` Auvergne-Rhône-Alpes, `93` PACA, `94` Corse.
