---
name: fr-geocode
description: Géocode une adresse française (texte → lat/lon, commune, code INSEE) ou fait l'inverse (lat/lon → adresse) via la Base Adresse Nationale (BAN). Trigger when user asks "où se trouve [adresse]", "code INSEE de [lieu]", "à quelle commune correspondent ces coordonnées", "geocode", "reverse geocode", ou cite une adresse ou des coordonnées GPS en France. Mots-clés - adresse, BAN, INSEE, citycode, géocodage, geocode, coordonnées GPS, latitude longitude.
allowed-tools: Bash(python *), Bash(python3 *)
---

# fr-geocode — Géocodage France (BAN)

Skill de base : convertit une adresse en coordonnées (et inversement) en s'appuyant sur la **Base Adresse Nationale** (api-adresse.data.gouv.fr).

Tous les autres skills d'urgence ont besoin de coordonnées pour fonctionner (Overpass, Météo, Hub'Eau…). Commence presque toujours par ici quand l'utilisateur donne un lieu en texte.

## Quand utiliser ce skill

- L'utilisateur dit "à Lyon", "12 rue de la Paix Paris", "mairie de Nantes" → forward geocoding.
- L'utilisateur donne des coordonnées GPS sans contexte → reverse geocoding pour obtenir commune, code INSEE.
- Un autre skill a besoin d'un code INSEE / d'une commune normalisée → passe par ici.

## Utilisation

Le script `geocode.py` accepte deux modes :

**Forward (adresse → coordonnées)** :
```bash
python skills/fr-geocode/geocode.py forward "12 rue de la Paix, 75002 Paris"
python skills/fr-geocode/geocode.py forward "mairie de Nantes" --limit 3
```

**Reverse (coordonnées → adresse)** :
```bash
python skills/fr-geocode/geocode.py reverse 48.8566 2.3522
```

## Format de sortie

JSON sur stdout, structure :
```json
{
  "query": "12 rue de la Paix, 75002 Paris",
  "results": [
    {
      "label": "12 Rue de la Paix 75002 Paris",
      "lat": 48.8694,
      "lon": 2.3318,
      "score": 0.97,
      "postcode": "75002",
      "city": "Paris",
      "citycode": "75102",
      "context": "75, Paris, Île-de-France",
      "type": "housenumber"
    }
  ]
}
```

Le champ `citycode` est le **code INSEE de la commune** (différent du code postal), c'est lui qu'il faut utiliser pour interroger geo.api.gouv.fr, l'INSEE, etc.

## Bonnes pratiques

- Si plusieurs résultats avec scores proches, demande à l'utilisateur de confirmer (ambiguïté).
- Score < 0.5 → résultat très incertain, signale-le à l'utilisateur.
- Pour les lieux d'intérêt (mairies, hôpitaux nommés), la BAN fonctionne souvent mais Overpass (skill fr-locate-infra) est parfois plus pertinent.
