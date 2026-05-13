"""Génère un rapport HTML autonome (carte Leaflet + synthèse) en orchestrant les skills du plugin.

Le HTML produit est totalement standalone (Leaflet via CDN, pas de build, pas de serveur).
Ouvre-le simplement dans un navigateur.

Usage :
    python report.py
    python report.py --address "1 rue de Rivoli, 75001 Paris"
    python report.py --address "..." --output rapport.html
"""

from __future__ import annotations

import argparse
import html
import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path

SKILLS_DIR = Path(__file__).parent / "skills"

LEVEL_COLORS = {
    "green": "#2ecc71",
    "yellow": "#f1c40f",
    "orange": "#e67e22",
    "red": "#e74c3c",
    "unknown": "#95a5a6",
}


def _load(skill: str, filename: str):
    path = SKILLS_DIR / skill / filename
    spec = importlib.util.spec_from_file_location(f"plugin_urgence.{skill}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _safe(label: str, fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        print(f"  [!] Échec de {label}: {type(e).__name__}: {e}", file=sys.stderr)
        return None


def collect(address: str) -> dict:
    print(f"Collecte des données pour : {address}", file=sys.stderr)

    geocode = _load("fr-geocode", "geocode.py")
    g = _safe("geocode", geocode.forward, address, limit=1)
    if not g or not g.get("results"):
        raise RuntimeError("Géocodage impossible — abandon")
    loc = g["results"][0]
    lat, lon, citycode = loc["lat"], loc["lon"], loc["citycode"]

    locate = _load("fr-locate-infra", "locate_infra.py")
    char = _load("fr-characterize-zone", "characterize.py")
    water = _load("fr-water-access", "water_access.py")
    weather = _load("fr-weather-alerts", "weather_alerts.py")
    health = _load("fr-health-alerts", "health_alerts.py")
    georisques = _load("fr-georisques", "georisques.py")
    vigicrues = _load("fr-vigicrues", "vigicrues.py")
    route = _load("fr-route", "route.py")

    infra = _safe("infra", locate.fetch_infrastructure, lat, lon, 1500, ["health", "emergency"])
    commune = _safe("commune", char.commune_info, citycode)
    sens = _safe("sensitive", char.sensitive_facilities, lat, lon, 2000)
    osm_water_data = _safe("osm_water", water.osm_water, lat, lon, 1500)
    wx = _safe("weather", weather.build_report, lat, lon, 3)
    h = _safe("health", health.build_report, lat, lon)
    risks = _safe("georisques", georisques.build_report, citycode, 5, 3)
    crues = _safe("vigicrues", vigicrues.build_report, lat, lon, 15, 6)

    # Itinéraires vers les 3 hôpitaux les plus proches (avec géométries pour la carte)
    hospitals = []
    if infra:
        hospitals = [x for x in infra["results"]["health"] if x["kind"] == "hospital"][:3]
    routes_with_geom = []
    for hp in hospitals:
        r = _safe(f"route to {hp.get('name')}", route.osrm_route, lat, lon, hp["lat"], hp["lon"], "full")
        if r and "error" not in r:
            routes_with_geom.append({
                "label": hp.get("name") or "(sans nom)",
                "distance_m": r["distance_m"],
                "duration_human": r["duration_human"],
                "geometry": r["geometry"],
            })

    return {
        "address": address,
        "location": {"lat": lat, "lon": lon, "label": loc["label"], "citycode": citycode, "score": loc["score"]},
        "infra": infra,
        "commune": commune,
        "sensitive": sens,
        "water": osm_water_data,
        "weather": wx,
        "health": h,
        "georisques": risks,
        "vigicrues": crues,
        "routes": routes_with_geom,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }


def _badge(level: str) -> str:
    if not level:
        level = "unknown"
    color = LEVEL_COLORS.get(level, LEVEL_COLORS["unknown"])
    return f'<span class="badge" style="background:{color}">{html.escape(level.upper())}</span>'


def render_html(d: dict) -> str:
    """Rend le HTML autonome (Leaflet via CDN)."""
    loc = d["location"]
    commune = d.get("commune") or {}
    sens = d.get("sensitive") or {}
    wx = d.get("weather") or {}
    h = d.get("health") or {}
    risks = d.get("georisques") or {}
    crues = d.get("vigicrues") or {}
    infra = d.get("infra") or {}
    water = d.get("water") or {}
    routes = d.get("routes") or []

    # Payload JS pour la carte
    map_payload = {
        "center": {"lat": loc["lat"], "lon": loc["lon"]},
        "infra_health": [
            {"name": x.get("name"), "lat": x["lat"], "lon": x["lon"], "kind": x["kind"]}
            for x in infra.get("results", {}).get("health", [])
        ],
        "infra_emergency": [
            {"name": x.get("name"), "lat": x["lat"], "lon": x["lon"], "kind": x["kind"]}
            for x in infra.get("results", {}).get("emergency", [])
        ],
        "drinking_water": [
            {"name": x.get("name"), "lat": x["lat"], "lon": x["lon"]}
            for x in water.get("results", {}).get("drinking_water", [])
        ],
        "ehpad": [
            {"name": x.get("name"), "lat": x["lat"], "lon": x["lon"]}
            for x in sens.get("results", {}).get("ehpad", [])
        ],
        "kindergarten": [
            {"name": x.get("name"), "lat": x["lat"], "lon": x["lon"]}
            for x in sens.get("results", {}).get("kindergarten", [])
        ],
        "vigicrues": [
            {
                "name": s.get("libelle"),
                "lat": s["lat"],
                "lon": s["lon"],
                "trend": s.get("trend_24h"),
                "height_m": s.get("latest_height_m"),
                "delta_m": s.get("delta_24h_m"),
            }
            for s in crues.get("stations", [])
        ],
        "routes": routes,
    }

    # Stats commune
    commune_name = commune.get("nom", "—") if commune else "—"
    commune_pop = f"{commune.get('population', 0):,}".replace(",", " ") if commune else "—"
    commune_surf = commune.get("surface_km2", "—") if commune else "—"
    commune_dens = commune.get("densite_hab_km2", "—") if commune else "—"

    # Niveaux d'alerte
    wx_level = wx.get("overall_level") if wx else "unknown"
    h_level = h.get("overall_level") if h else "unknown"

    # Risques recensés (top 8)
    risques_recenses = risks.get("risques_recenses", [])[:8] if risks else []
    catnat_total = (risks.get("catnat") or {}).get("total", 0) if risks else 0
    icpe_total = (risks.get("icpe") or {}).get("total", 0) if risks else 0
    radon_label = (risks.get("radon") or {}).get("label", "—") if risks else "—"

    # Stations Vigicrues
    vigicrues_summary = ""
    if crues and crues.get("stations"):
        trend_colors = {"rising": "#e74c3c", "falling": "#27ae60", "stable": "#7f8c8d", "unknown": "#bdc3c7"}
        rows = []
        for s in crues["stations"][:5]:
            trend = s.get("trend_24h") or "unknown"
            color = trend_colors.get(trend, "#bdc3c7")
            h_m = s.get("latest_height_m")
            d_m = s.get("delta_24h_m")
            height_cell = f"{h_m} m" if h_m is not None else "—"
            trend_cell = f"{trend} ({d_m:+.2f} m)" if d_m is not None else trend
            rows.append(
                "<tr>"
                f"<td>{html.escape(s.get('libelle') or '—')}</td>"
                f"<td>{html.escape(str(s.get('cours_eau') or '—'))}</td>"
                f"<td>{height_cell}</td>"
                f"<td style='color:{color};font-weight:600'>{trend_cell}</td>"
                "</tr>"
            )
        vigicrues_summary = (
            "<table><thead><tr><th>Station</th><th>Cours d'eau</th><th>Niveau</th><th>Tendance 24 h</th></tr></thead>"
            "<tbody>" + "".join(rows) + "</tbody></table>"
        )

    payload_json = json.dumps(map_payload, ensure_ascii=False)

    return f"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Rapport d'urgence — {html.escape(commune_name)}</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <style>
    * {{ box-sizing: border-box; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; background: #f5f6fa; color: #2c3e50; }}
    header {{ background: #2c3e50; color: white; padding: 18px 28px; }}
    header h1 {{ margin: 0; font-size: 22px; font-weight: 600; }}
    header .meta {{ font-size: 13px; opacity: 0.75; margin-top: 4px; }}
    main {{ display: grid; grid-template-columns: 1fr 1fr; gap: 18px; padding: 18px; }}
    @media (max-width: 1000px) {{ main {{ grid-template-columns: 1fr; }} }}
    .card {{ background: white; border-radius: 6px; padding: 18px; box-shadow: 0 1px 3px rgba(0,0,0,.08); }}
    .card h2 {{ margin: 0 0 12px; font-size: 15px; text-transform: uppercase; letter-spacing: 0.5px; color: #7f8c8d; }}
    .badge {{ display: inline-block; padding: 3px 9px; border-radius: 3px; color: white; font-size: 12px; font-weight: 600; letter-spacing: 0.5px; }}
    .kpi {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }}
    .kpi .k {{ background: #ecf0f1; padding: 10px; border-radius: 4px; }}
    .kpi .k label {{ display: block; font-size: 11px; color: #7f8c8d; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px; }}
    .kpi .k strong {{ font-size: 19px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    th, td {{ text-align: left; padding: 6px 8px; border-bottom: 1px solid #ecf0f1; }}
    th {{ color: #7f8c8d; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; }}
    ul.risques {{ list-style: none; padding: 0; margin: 0; display: flex; flex-wrap: wrap; gap: 6px; }}
    ul.risques li {{ background: #fdecea; color: #c0392b; padding: 4px 9px; border-radius: 3px; font-size: 12px; }}
    #map {{ height: 520px; border-radius: 6px; }}
    .legend {{ background: white; padding: 8px 10px; line-height: 1.5; font-size: 12px; box-shadow: 0 1px 3px rgba(0,0,0,.2); border-radius: 4px; }}
    .legend i {{ display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 6px; vertical-align: middle; }}
  </style>
</head>
<body>
  <header>
    <h1>Rapport d'urgence — {html.escape(commune_name)}</h1>
    <div class="meta">{html.escape(loc['label'])} &middot; {loc['lat']:.5f}, {loc['lon']:.5f} &middot; généré le {html.escape(d['generated_at'])}</div>
  </header>
  <main>
    <section class="card" style="grid-column: 1/-1;">
      <h2>Carte opérationnelle</h2>
      <div id="map"></div>
    </section>

    <section class="card">
      <h2>Lieu</h2>
      <div class="kpi">
        <div class="k"><label>Commune</label><strong>{html.escape(commune_name)}</strong></div>
        <div class="k"><label>Population</label><strong>{commune_pop}</strong></div>
        <div class="k"><label>Surface</label><strong>{commune_surf} km²</strong></div>
        <div class="k"><label>Densité</label><strong>{commune_dens} hab/km²</strong></div>
      </div>
    </section>

    <section class="card">
      <h2>Niveaux d'alerte</h2>
      <div class="kpi">
        <div class="k"><label>Météo</label><strong>{_badge(wx_level)}</strong></div>
        <div class="k"><label>Sanitaire</label><strong>{_badge(h_level)}</strong></div>
        <div class="k"><label>AQI européen</label><strong>{(h.get('air_quality') or {}).get('european_aqi', '—') if h else '—'}</strong></div>
        <div class="k"><label>Pollen dominant</label><strong>{(h.get('pollen') or {}).get('dominant', '—') if h else '—'}</strong></div>
      </div>
    </section>

    <section class="card">
      <h2>Vulnérabilités proches (rayon 2 km)</h2>
      <div class="kpi">
        <div class="k"><label>EHPAD</label><strong>{sens.get('counts', {}).get('ehpad', 0)}</strong></div>
        <div class="k"><label>Crèches</label><strong>{sens.get('counts', {}).get('kindergarten', 0)}</strong></div>
        <div class="k"><label>Écoles</label><strong>{sens.get('counts', {}).get('school', 0)}</strong></div>
        <div class="k"><label>Score vulnérabilité</label><strong>{sens.get('vulnerability_score', '—')}</strong></div>
      </div>
    </section>

    <section class="card">
      <h2>Profil de risque (Géorisques)</h2>
      <div class="kpi">
        <div class="k"><label>Risques recensés</label><strong>{len(risks.get('risques_recenses', []))}</strong></div>
        <div class="k"><label>Arrêtés CatNat</label><strong>{catnat_total}</strong></div>
        <div class="k"><label>ICPE</label><strong>{icpe_total}</strong></div>
        <div class="k"><label>Radon</label><strong>{html.escape(str(radon_label))}</strong></div>
      </div>
      <ul class="risques" style="margin-top: 12px;">
        {''.join(f'<li>{html.escape(r.get("label",""))}</li>' for r in risques_recenses)}
      </ul>
    </section>

    <section class="card" style="grid-column: 1/-1;">
      <h2>Cours d'eau — Hub'Eau / Vigicrues</h2>
      {vigicrues_summary or '<p style="color:#7f8c8d">Aucune station dans le rayon.</p>'}
    </section>

    <section class="card" style="grid-column: 1/-1;">
      <h2>Hôpitaux accessibles (les 3 plus rapides en voiture)</h2>
      <table><thead><tr><th>Hôpital</th><th>Distance</th><th>Durée</th></tr></thead><tbody>
      {''.join(f'<tr><td>{html.escape(r["label"])}</td><td>{r["distance_m"]:.0f} m</td><td>{html.escape(r["duration_human"])}</td></tr>' for r in routes)}
      </tbody></table>
    </section>
  </main>

  <script>
  const data = {payload_json};
  const map = L.map('map').setView([data.center.lat, data.center.lon], 14);
  L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap'
  }}).addTo(map);

  // Centre (incident)
  L.marker([data.center.lat, data.center.lon], {{
    icon: L.divIcon({{ html: '🚨', className: 'incident-marker', iconSize: [26, 26] }})
  }}).addTo(map).bindPopup('<strong>Point d\\'analyse</strong>');

  const dot = (color) => L.divIcon({{
    html: `<div style="background:${{color}};width:12px;height:12px;border-radius:50%;border:2px solid white;box-shadow:0 0 3px rgba(0,0,0,.5)"></div>`,
    className: '', iconSize: [12, 12]
  }});

  function addGroup(items, color, label) {{
    items.forEach(x => {{
      L.marker([x.lat, x.lon], {{ icon: dot(color) }})
        .addTo(map).bindPopup(`<strong>${{label}}</strong><br>${{x.name || '(sans nom)'}}`);
    }});
  }}

  addGroup(data.infra_health.filter(x => x.kind === 'hospital'), '#e74c3c', 'Hôpital');
  addGroup(data.infra_emergency, '#e67e22', 'Secours');
  addGroup(data.ehpad, '#9b59b6', 'EHPAD');
  addGroup(data.kindergarten, '#f1c40f', 'Crèche');
  addGroup(data.drinking_water, '#3498db', "Point d'eau");

  // Stations Vigicrues (avec couleur selon la tendance)
  data.vigicrues.forEach(s => {{
    const color = {{ rising: '#e74c3c', falling: '#27ae60', stable: '#95a5a6' }}[s.trend] || '#bdc3c7';
    L.circle([s.lat, s.lon], {{ radius: 200, color: color, fillColor: color, fillOpacity: 0.3, weight: 2 }})
      .addTo(map).bindPopup(`<strong>${{s.name}}</strong><br>${{s.height_m ?? '—'}} m (${{s.trend}})`);
  }});

  // Itinéraires
  data.routes.forEach((r, i) => {{
    const colors = ['#e74c3c', '#e67e22', '#f39c12'];
    if (r.geometry) {{
      L.geoJSON(r.geometry, {{ style: {{ color: colors[i] || '#3498db', weight: 4, opacity: 0.7 }} }})
        .addTo(map).bindPopup(`<strong>${{r.label}}</strong><br>${{r.distance_m.toFixed(0)}} m – ${{r.duration_human}}`);
    }}
  }});

  // Légende
  const legend = L.control({{ position: 'bottomright' }});
  legend.onAdd = function() {{
    const div = L.DomUtil.create('div', 'legend');
    div.innerHTML = `
      <i style="background:#e74c3c"></i> Hôpital<br>
      <i style="background:#e67e22"></i> Secours (pompiers/police)<br>
      <i style="background:#9b59b6"></i> EHPAD<br>
      <i style="background:#f1c40f"></i> Crèche<br>
      <i style="background:#3498db"></i> Point d'eau<br>
      <i style="background:#27ae60"></i> Cours d'eau (en baisse)
    `;
    return div;
  }};
  legend.addTo(map);
  </script>
</body>
</html>
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Génère un rapport HTML d'urgence.")
    parser.add_argument("--address", default="29 rue de Strasbourg, 44000 Nantes")
    parser.add_argument("--output", default="report.html")
    args = parser.parse_args(argv)

    try:
        data = collect(args.address)
    except RuntimeError as e:
        print(f"ERREUR : {e}", file=sys.stderr)
        return 1

    html_out = render_html(data)
    Path(args.output).write_text(html_out, encoding="utf-8")
    print(f"Rapport généré : {Path(args.output).resolve()}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
