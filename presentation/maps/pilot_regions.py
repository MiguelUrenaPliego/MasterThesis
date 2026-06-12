"""
buildings_map.py
Loads Guatemala / San Jose / Santo Domingo pilot region GeoPackages and builds
an interactive Folium HTML map with two dropdowns:
  - City selector
  - Column / attribute selector (with dynamically updating legend)

Background: Google Hybrid satellite tiles at 0.5 opacity.

Usage:
    pip install folium geopandas
    python buildings_map.py
"""

import json
import folium
import geopandas as gpd
import numpy as np

# ─────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────
MODEL_RESULTS = False

FILES = {
    "Guatemala":     "/home/miguel/Documents/UNI/Master/2/TFM/presentation/maps/vector/guatemala_pilot_region.gpkg",
    "San Jose":      "/home/miguel/Documents/UNI/Master/2/TFM/presentation/maps/vector/san_jose_pilot_region.gpkg",
    "Santo Domingo": "/home/miguel/Documents/UNI/Master/2/TFM/presentation/maps/vector/santo_domingo_pilot_region.gpkg",
}

GOOGLE_HYBRID = "https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}"

# ─────────────────────────────────────────
# COLUMN CONFIGURATION
# ─────────────────────────────────────────
# type: "numeric"          -> red(vmin) -> yellow -> green(vmax)
#       "numeric_reverse"  -> green(vmin) -> yellow -> red(vmax)
#       "circular"         -> hue wheel 0-360 (0 == 360)
#       "categorical"      -> distinct random (deterministic) colors
#
# vmin / vmax: if given, fixed; if None, computed from the data (global
# across the three cities) at build time.

COLUMN_CONFIG = {
    "height":                          {"type": "numeric",         "vmin": 3, "vmax": 30, "label": "Height (m)"},
    "n_storeys":                       {"type": "numeric",         "vmin": 1, "vmax": 10, "label": "N. storeys"},
    "year":                            {"type": "numeric",         "vmin": 1975, "vmax": 2015, "label": "Year"},
    "code_quality":                    {"type": "categorical",      "label": "Code quality"},
    "structural_system":               {"type": "categorical",      "label": "Structural system"},
    "simplified_structural_system":    {"type": "categorical",      "label": "Simplified structural system"},
    "roof":                            {"type": "categorical",      "label": "Roof"},
    "area":                            {"type": "numeric",         "vmin": None, "vmax": None, "label": "Area (m²)"},
    "perimeter":                       {"type": "numeric",         "vmin": None, "vmax": None, "label": "Perimeter (m)"},
    "EC8_eccentricity_ratio":          {"type": "numeric",         "vmin": 0,    "vmax": 0.4,  "label": "EC8 eccentricity ratio"},
    "EC8_radius_ratio":                {"type": "numeric",         "vmin": 0,    "vmax": 1,    "label": "EC8 radius ratio"},
    "EC8_compactness":                 {"type": "numeric_reverse", "vmin": 0.80, "vmax": 1,    "label": "EC8 compactness"},
    "EC8_direction_eccentricity":      {"type": "circular",         "label": "EC8 direction eccentricity (°)"},
    "CR_eccentricity_ratio":           {"type": "numeric",         "vmin": 0,    "vmax": 0.4,  "label": "CR eccentricity ratio"},
    "CR_direction_eccentricity":       {"type": "circular",         "label": "CR direction eccentricity (°)"},
    "NTC_setback_ratio":               {"type": "numeric",         "vmin": 0,    "vmax": 0.4,  "label": "NTC setback ratio"},
    "NTC_hole_ratio":                  {"type": "numeric",         "vmin": 0,    "vmax": 0.4,  "label": "NTC hole ratio"},
    "ASCE7_setback_ratio":             {"type": "numeric",         "vmin": 0,    "vmax": 0.4,  "label": "ASCE7 setback ratio"},
    "ASCE7_hole_ratio":                {"type": "numeric",         "vmin": 0,    "vmax": 0.4,  "label": "ASCE7 hole ratio"},
    "ASCE7_parallelity_angle":         {"type": "numeric_reverse", "vmin": 0.8,  "vmax": 1,    "label": "ASCE7 parallelity angle"},
    "GNDT_main_shape_slenderness":     {"type": "numeric",         "vmin": 1,    "vmax": 4,    "label": "GNDT main shape slenderness"},
    "GNDT_setback_ratio":              {"type": "numeric",         "vmin": 0,    "vmax": 0.4,  "label": "GNDT setback ratio"},
    "GNDT_eccentricity_ratio":         {"type": "numeric",         "vmin": 0,    "vmax": 0.4,  "label": "GNDT eccentricity ratio"},
    "GNDT_setback_slenderness":        {"type": "numeric",         "vmin": 1,    "vmax": 4,    "label": "GNDT setback slenderness"},
    "slenderness_elevation":           {"type": "numeric",         "vmin": 1,    "vmax": 4,    "label": "Slenderness (elevation)"},
    "slenderness_inertia":             {"type": "numeric",         "vmin": 1,    "vmax": 4,    "label": "Slenderness (inertia)"},
    "inertia_direction":               {"type": "circular",         "label": "Inertia direction (°)"},
    "slenderness_bbox":                {"type": "numeric",         "vmin": 1,    "vmax": 4,    "label": "Slenderness (bbox)"},
    "bbox_direction":                  {"type": "circular",         "label": "Bbox direction (°)"},
    "slenderness_circunscribed":       {"type": "numeric",         "vmin": 1,    "vmax": 4,    "label": "Slenderness (circumscribed)"},
    "circunscribed_direction":         {"type": "circular",         "label": "Circumscribed direction (°)"},
    "inertia_vs_circle":               {"type": "numeric",         "vmin": None, "vmax": None, "label": "Inertia vs circle"},
    "fsi":                             {"type": "categorical",      "label": "FSI"},
    "regularity_boolean":              {"type": "categorical",      "label": "Regularity"},
    "contact_force":                   {"type": "numeric",         "vmin": None, "vmax": None, "label": "Contact force"},
    "contact_confinement_ratio":       {"type": "numeric",         "vmin": None, "vmax": None, "label": "Contact confinement ratio"},
    "contact_angular_acc":             {"type": "numeric",         "vmin": None, "vmax": None, "label": "Contact angular acceleration"},
    "contact_angle":                   {"type": "circular",         "label": "Contact angle (°)"},
    "relative_position":               {"type": "categorical",      "label": "Relative position"},
}

if MODEL_RESULTS:
    COLUMN_CONFIG["model_LR_structural_system"]      = {"type": "categorical", "label": "LR structural system (model)"}
    COLUMN_CONFIG["model_XGBoost_structural_system"] = {"type": "categorical", "label": "XGBoost structural system (model)"}

NUMERIC_TYPES = ("numeric", "numeric_reverse")
CIRCULAR_COLS = [c for c, cfg in COLUMN_CONFIG.items() if cfg["type"] == "circular"]
CATEGORICAL_COLS = [c for c, cfg in COLUMN_CONFIG.items() if cfg["type"] == "categorical"]

ALL_COLUMNS = list(COLUMN_CONFIG.keys())

# ─────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────
gdfs = {}
for city, path in FILES.items():
    try:
        gdf = gpd.read_file(path).to_crs(4326)
        print(f"  Loaded {city}: {len(gdf)} features")
    except Exception as e:
        print(f"  WARN: could not load {city} ({path}): {e}")
        gdf = gpd.GeoDataFrame(columns=["geometry"], geometry="geometry", crs=4326)
    gdfs[city] = gdf

# ─────────────────────────────────────────
# COMPUTE GLOBAL VMIN/VMAX FOR NUMERIC COLS WITHOUT FIXED RANGE
# ─────────────────────────────────────────
for col, cfg in COLUMN_CONFIG.items():
    if cfg["type"] in NUMERIC_TYPES and (cfg.get("vmin") is None or cfg.get("vmax") is None):
        vals = []
        for gdf in gdfs.values():
            if col in gdf.columns:
                s = gdf[col].dropna()
                s = s[np.isfinite(s)] if len(s) else s
                if len(s):
                    vals.append(s)
        if vals:
            allvals = np.concatenate([v.values for v in vals])
            cfg["vmin"] = float(np.nanmin(allvals))
            cfg["vmax"] = float(np.nanmax(allvals))
        else:
            cfg["vmin"], cfg["vmax"] = 0.0, 1.0

# ─────────────────────────────────────────
# BUILD GEOJSON PER CITY (only relevant columns + geometry)
# ─────────────────────────────────────────
geojson_data = {}
city_centers = {}

for city, gdf in gdfs.items():
    if len(gdf) == 0:
        geojson_data[city] = {"type": "FeatureCollection", "features": []}
        city_centers[city] = (0, 0)
        continue

    keep_cols = [c for c in ALL_COLUMNS if c in gdf.columns]
    sub = gdf[keep_cols + ["geometry"]].copy()

    # Replace NaN/Inf with None for JSON serialization, cast numpy types
    def clean(v):
        if v is None:
            return None
        if isinstance(v, float) and (np.isnan(v) or np.isinf(v)):
            return None
        if isinstance(v, (np.integer,)):
            return int(v)
        if isinstance(v, (np.floating,)):
            return float(v)
        if isinstance(v, (np.bool_,)):
            return bool(v)
        return v

    features = []
    for _, row in sub.iterrows():
        geom = row.geometry
        if geom is None or geom.is_empty:
            continue
        props = {c: clean(row[c]) for c in keep_cols}
        features.append({
            "type": "Feature",
            "geometry": geom.__geo_interface__,
            "properties": props,
        })

    geojson_data[city] = {"type": "FeatureCollection", "features": features}

    b = gdf.total_bounds  # [minx, miny, maxx, maxy]
    city_centers[city] = ((b[1] + b[3]) / 2, (b[0] + b[2]) / 2)

# Global initial center
all_centers = [c for c in city_centers.values() if c != (0, 0)]
if all_centers:
    g_lat = sum(c[0] for c in all_centers) / len(all_centers)
    g_lon = sum(c[1] for c in all_centers) / len(all_centers)
else:
    g_lat, g_lon = 0, 0

# ─────────────────────────────────────────
# BUILD MAP
# ─────────────────────────────────────────
m = folium.Map(location=[g_lat, g_lon], zoom_start=15, tiles=None,
                max_zoom=22, control_scale=True)

folium.TileLayer(
    tiles=GOOGLE_HYBRID,
    name="Google Hybrid",
    attr="Google",
    overlay=False, control=True,
    max_zoom=22, max_native_zoom=20,
    show=True,
    opacity=0.5,
).add_to(m)

folium.LayerControl(collapsed=False, position="topright").add_to(m)

# ─────────────────────────────────────────
# EMBED DATA AS JS
# ─────────────────────────────────────────
js_lines = ["<script>"]
js_lines.append("var BUILDING_DATA = " + json.dumps(geojson_data) + ";")
js_lines.append("var CITY_CENTERS = " + json.dumps(
    {c: {"lat": v[0], "lon": v[1]} for c, v in city_centers.items()}
) + ";")
js_lines.append("var COLUMN_CONFIG = " + json.dumps(COLUMN_CONFIG) + ";")
js_lines.append("var CITIES = " + json.dumps(list(FILES.keys())) + ";")
js_lines.append("</script>")
m.get_root().html.add_child(folium.Element("\n".join(js_lines)))

# ─────────────────────────────────────────
# DROPDOWN UI
# ─────────────────────────────────────────
city_options = "\n".join(f'      <option value="{c}">{c}</option>' for c in FILES.keys())
column_options = "\n".join(
    f'      <option value="{c}">{cfg["label"]}</option>' for c, cfg in COLUMN_CONFIG.items()
)

dropdown_html = f"""
<div id="map-controls" style="
    position:fixed; top:10px; left:50%; transform:translateX(-50%);
    z-index:9999; background:white; padding:12px 20px;
    border:1px solid #ccc; border-radius:10px;
    font-family:sans-serif; font-size:13px;
    box-shadow:0 3px 12px rgba(0,0,0,.2);
    display:flex; gap:20px; align-items:flex-end;">
  <div>
    <label style="font-weight:bold;display:block;margin-bottom:5px;">City</label>
    <select id="citySelect" style="width:160px;font-size:13px;padding:4px 6px;">
{city_options}
    </select>
  </div>
  <div>
    <label style="font-weight:bold;display:block;margin-bottom:5px;">Layer / column</label>
    <select id="columnSelect" style="width:260px;font-size:13px;padding:4px 6px;">
{column_options}
    </select>
  </div>
</div>
"""
m.get_root().html.add_child(folium.Element(dropdown_html))

# ─────────────────────────────────────────
# LEGEND CONTAINER (filled dynamically)
# ─────────────────────────────────────────
legend_html = """
<div id="map-legend" style="
    position:fixed; bottom:30px; left:15px; z-index:9999;
    background:white; padding:12px 16px;
    border:1px solid #bbb; border-radius:10px;
    font-family:sans-serif; font-size:13px;
    box-shadow:0 2px 10px rgba(0,0,0,.15); min-width:200px;">
  <b id="legend-title" style="font-size:14px;">Legend</b>
  <div id="legend-body" style="margin-top:8px;"></div>
</div>
"""
m.get_root().html.add_child(folium.Element(legend_html))

# ─────────────────────────────────────────
# MAIN JS LOGIC
# ─────────────────────────────────────────
main_js = """
<script>
(function() {
  var currentLayer = null;
  // Cache of categorical color maps: catColors[city][column][value] = hex
  var catColors = {};

  function getLeafletMap() {
    var keys = Object.keys(window).filter(function(k){ return k.startsWith('map_'); });
    return keys.length ? window[keys[0]] : null;
  }

  // --- Color helpers ---------------------------------------------------

  function hslToHex(h, s, l) {
    s /= 100; l /= 100;
    var c = (1 - Math.abs(2 * l - 1)) * s;
    var x = c * (1 - Math.abs((h / 60) % 2 - 1));
    var m = l - c / 2;
    var r=0, g=0, b=0;
    if (h < 60)       { r=c; g=x; b=0; }
    else if (h < 120) { r=x; g=c; b=0; }
    else if (h < 180) { r=0; g=c; b=x; }
    else if (h < 240) { r=0; g=x; b=c; }
    else if (h < 300) { r=x; g=0; b=c; }
    else              { r=c; g=0; b=x; }
    var R = Math.round((r+m)*255), G = Math.round((g+m)*255), B = Math.round((b+m)*255);
    return "#" + [R,G,B].map(function(v){ return v.toString(16).padStart(2,'0'); }).join("");
  }

  // Red(low) -> Yellow(mid) -> Green(high), or reversed
  function rygColor(t, reverse) {
    // t in [0,1]
    if (!reverse) t = 1 - t;
    // hue 0 (red) -> 60 (yellow) -> 120 (green)
    var hue = t * 120;
    return hslToHex(hue, 80, 50);
  }

  // Hue wheel for circular columns (0-360 deg, 0 == 360)
  function circularColor(deg) {
    var hue = ((deg % 360) + 360) % 360;
    return hslToHex(hue, 75, 50);
  }

  // Deterministic distinct colors for categorical values using golden-ratio hue stepping
  function categoricalColor(city, col, value) {
    catColors[city] = catColors[city] || {};
    catColors[city][col] = catColors[city][col] || {};
    var map = catColors[city][col];
    if (value === null || value === undefined) return "#999999";
    if (!(value in map)) {
      var n = Object.keys(map).length;
      var hue = (n * 137.508) % 360; // golden angle
      map[value] = hslToHex(hue, 65, 50);
    }
    return map[value];
  }

  function getValueColor(city, col, value, cfg) {
    if (value === null || value === undefined) return "#cccccc";
    if (cfg.type === "numeric" || cfg.type === "numeric_reverse") {
      var vmin = cfg.vmin, vmax = cfg.vmax;
      var t = (vmax > vmin) ? (value - vmin) / (vmax - vmin) : 0.5;
      t = Math.max(0, Math.min(1, t));
      return rygColor(t, cfg.type === "numeric_reverse");
    }
    if (cfg.type === "circular") {
      return circularColor(value);
    }
    if (cfg.type === "categorical") {
      return categoricalColor(city, col, value);
    }
    return "#999999";
  }

  function styleFeature(city, col, cfg) {
    return function(feature) {
      var v = feature.properties[col];
      var color = getValueColor(city, col, v, cfg);
      return { fillColor: color, fillOpacity: 0.75, color: "#222222", weight: 1, opacity: 0.6 };
    };
  }

  // --- Legend ------------------------------------------------------------

  function buildLegend(city, col, cfg) {
    var title = document.getElementById('legend-title');
    var body  = document.getElementById('legend-body');
    title.innerText = cfg.label || col;
    body.innerHTML = "";

    if (cfg.type === "numeric" || cfg.type === "numeric_reverse") {
      var stops = [];
      for (var i = 0; i <= 10; i++) {
        stops.push(rygColor(i/10, cfg.type === "numeric_reverse") + " " + (i*10) + "%");
      }
      var grad = stops.join(",");
      body.innerHTML =
        '<div style="width:200px;height:14px;background:linear-gradient(to right,' + grad + ');' +
        'border:1px solid #aaa;border-radius:3px;"></div>' +
        '<div style="display:flex;justify-content:space-between;width:200px;margin-top:3px;">' +
        '<span>' + cfg.vmin.toFixed(2) + '</span><span>' + cfg.vmax.toFixed(2) + '</span></div>';
    } else if (cfg.type === "circular") {
      var hstops = [];
      for (var h = 0; h <= 360; h += 30) hstops.push(circularColor(h) + " " + (h/360*100) + "%");
      var hgrad = hstops.join(",");
      body.innerHTML =
        '<div style="width:200px;height:14px;background:linear-gradient(to right,' + hgrad + ');' +
        'border:1px solid #aaa;border-radius:3px;"></div>' +
        '<div style="display:flex;justify-content:space-between;width:200px;margin-top:3px;">' +
        '<span>0°</span><span>180°</span><span>360°</span></div>';
    } else if (cfg.type === "categorical") {
      // gather unique values present for this city/column to assign + display colors
      var data = BUILDING_DATA[city];
      var seen = {};
      var order = [];
      if (data) {
        data.features.forEach(function(f) {
          var v = f.properties[col];
          var key = (v === null || v === undefined) ? "(none)" : String(v);
          if (!(key in seen)) { seen[key] = true; order.push(v); }
        });
      }
      order.forEach(function(v) {
        var color = (v === null || v === undefined) ? "#999999" : categoricalColor(city, col, v);
        var label = (v === null || v === undefined) ? "(none)" : String(v);
        body.innerHTML +=
          '<div style="display:flex;align-items:center;margin-top:4px;">' +
          '<div style="width:14px;height:14px;background:' + color + ';border:1px solid #555;margin-right:6px;"></div>' +
          '<span>' + label + '</span></div>';
      });
      if (order.length === 0) {
        body.innerHTML = '<i>No data</i>';
      }
    }
  }

  // --- Tooltip field list (always show key attributes + selected column) -

  function tooltipFields(col) {
    var base = ["height", "n_storeys", "structural_system", "roof"];
    if (base.indexOf(col) === -1) base.push(col);
    return base;
  }

  // --- Update map ----------------------------------------------------------

  function updateMap() {
    var lmap = getLeafletMap();
    if (!lmap) { setTimeout(updateMap, 300); return; }

    var city = document.getElementById('citySelect').value;
    var col  = document.getElementById('columnSelect').value;
    var cfg  = COLUMN_CONFIG[col];

    if (currentLayer) { lmap.removeLayer(currentLayer); currentLayer = null; }

    var data = BUILDING_DATA[city];
    if (data && data.features && data.features.length > 0) {
      var fields = tooltipFields(col).filter(function(f) {
        return data.features[0].properties.hasOwnProperty(f);
      });
      currentLayer = L.geoJSON(data, {
        style: styleFeature(city, col, cfg),
        onEachFeature: function(feature, layer) {
          var rows = fields.map(function(f) {
            var v = feature.properties[f];
            return '<b>' + f + '</b>: ' + (v === null || v === undefined ? '-' : v);
          }).join('<br>');
          layer.bindTooltip(rows, {sticky: true});
        }
      }).addTo(lmap);
    }

    buildLegend(city, col, cfg);

    var c = CITY_CENTERS[city];
    if (c && (c.lat !== 0 || c.lon !== 0)) lmap.setView([c.lat, c.lon], 16);
  }

  function init() {
    var lmap = getLeafletMap();
    if (!lmap) { setTimeout(init, 300); return; }
    document.getElementById('citySelect').addEventListener('change', updateMap);
    document.getElementById('columnSelect').addEventListener('change', updateMap);
    lmap.setMaxZoom(22);
    updateMap();
  }

  setTimeout(init, 800);
})();
</script>
"""
m.get_root().html.add_child(folium.Element(main_js))

# ─────────────────────────────────────────
# SAVE
# ─────────────────────────────────────────
out = "/home/miguel/Documents/UNI/Master/2/TFM/presentation/maps/pilot_regions_map.html"
m.save(out)
print(f"\n✓ Saved → {out}")