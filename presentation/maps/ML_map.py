"""
ml_results_map.py

1. Loads the 3 pilot-region area GeoDataFrames and the 5 ML-model output
   GeoDataFrames.
2. Renames columns:
     - area gdfs:  simplified_structural_system -> ground_truth_structural_system
     - model gdfs: simplified_structural_system -> {model_name}_structural_system
3. Spatially matches each model gdf to each area gdf (centroid-in-polygon)
   and copies {model_name}_structural_system into the area gdf (None where
   there's no match).
4. Creates {model_name}_error = (model == ground_truth), None if either side
   is None.
5. Builds an interactive Folium map with:
     - Area dropdown (Guatemala / San Jose / Santo Domingo)
     - Column dropdown (ground truth, each model's prediction, each model's
       error)
   Structural-system columns use a shared, non-repeating random color map
   (transparent for None). Error columns: green = True, red = False,
   transparent = None.

Usage:
    pip install folium geopandas
    python ml_results_map.py
"""

import json
import folium
import geopandas as gpd
import numpy as np

# ─────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────
AREA_FILES = {
    "Guatemala":     "/home/miguel/Documents/UNI/Master/2/TFM/presentation/maps/vector/guatemala_pilot_region.gpkg",
    "San Jose":      "/home/miguel/Documents/UNI/Master/2/TFM/presentation/maps/vector/san_jose_pilot_region.gpkg",
    "Santo Domingo": "/home/miguel/Documents/UNI/Master/2/TFM/presentation/maps/vector/santo_domingo_pilot_region.gpkg",
}

MODEL_FILES = {
    "CatBoost":           "/home/miguel/Documents/UNI/Master/2/TFM/presentation/maps/vector/MLoutput/test_output_CatBoost.gpkg",
    "LogisticRegression": "/home/miguel/Documents/UNI/Master/2/TFM/presentation/maps/vector/MLoutput/test_output_LogisticRegression.gpkg",
    "RandomForest":       "/home/miguel/Documents/UNI/Master/2/TFM/presentation/maps/vector/MLoutput/test_output_RandomForest.gpkg",
    "SVC":                "/home/miguel/Documents/UNI/Master/2/TFM/presentation/maps/vector/MLoutput/test_output_SVC.gpkg",
    "XGBoost":            "/home/miguel/Documents/UNI/Master/2/TFM/presentation/maps/vector/MLoutput/test_output_XGBoost.gpkg",
}

GOOGLE_HYBRID = "https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}"

GREEN = "#2ecc71"   # error == False -> match -> green... see note below
RED   = "#e74c3c"
TRANSPARENT = "#000000"  # color irrelevant when fillOpacity = 0

# ─────────────────────────────────────────
# 1) LOAD AREA GEODATAFRAMES + RENAME GROUND TRUTH COLUMN
# ─────────────────────────────────────────
area_gdfs = {}
for area, path in AREA_FILES.items():
    gdf = gpd.read_file(path)
    if "simplified_structural_system" in gdf.columns:
        gdf = gdf.rename(columns={"simplified_structural_system": "ground_truth_structural_system"})
    else:
        print(f"  WARN: 'simplified_structural_system' not found in {area} area gdf")
        gdf["ground_truth_structural_system"] = None
    area_gdfs[area] = gdf
    print(f"Loaded area '{area}': {len(gdf)} features")

# ─────────────────────────────────────────
# 2) LOAD MODEL OUTPUT GEODATAFRAMES + RENAME PREDICTION COLUMN
# ─────────────────────────────────────────
# --- REAL ML OUTPUTS (commented out for now) ---------------------------
# model_gdfs = {}
# for model_name, path in MODEL_FILES.items():
#     gdf = gpd.read_file(path)
#     pred_col = f"{model_name}_structural_system"
#     if "simplified_structural_system" in gdf.columns:
#         gdf = gdf.rename(columns={"simplified_structural_system": pred_col})
#     else:
#         print(f"  WARN: 'simplified_structural_system' not found in model gdf '{model_name}'")
#         gdf[pred_col] = None
#     model_gdfs[model_name] = gdf
#     print(f"Loaded model '{model_name}': {len(gdf)} features")

# ─────────────────────────────────────────
# 3) (SKIPPED) SPATIAL MATCH OF REAL MODEL OUTPUTS
# ─────────────────────────────────────────
# --- REAL SPATIAL MATCHING (commented out for now) ----------------------
# for area, area_gdf in area_gdfs.items():
#     base_crs = area_gdf.crs
#     for model_name, model_gdf in model_gdfs.items():
#         pred_col = f"{model_name}_structural_system"
#         mg = model_gdf
#         if mg.crs != base_crs:
#             mg = mg.to_crs(base_crs)
#         pts = gpd.GeoDataFrame(
#             {pred_col: mg[pred_col].values},
#             geometry=mg.geometry.centroid,
#             crs=base_crs,
#         )
#         joined = gpd.sjoin(
#             pts, area_gdf[["geometry"]],
#             how="left", predicate="within"
#         )
#         joined = joined.dropna(subset=["index_right"])
#         joined = joined.drop_duplicates(subset=["index_right"], keep="first")
#         mapping = joined.set_index("index_right")[pred_col]
#         area_gdf[pred_col] = area_gdf.index.map(mapping)
#         area_gdf[pred_col] = area_gdf[pred_col].where(area_gdf[pred_col].notna(), None)
#     area_gdfs[area] = area_gdf

# ─────────────────────────────────────────
# 2-3) PLACEHOLDER: SYNTHETIC "PREDICTIONS"
# ─────────────────────────────────────────
# For now, instead of loading/matching the real model outputs, each model's
# prediction column is just a copy of ground_truth_structural_system, with
# ~20% of rows randomly reassigned to a *different* category (so each model
# is ~80% "correct" by construction). Replace this block with the real
# loading/matching code above once the real ML outputs are ready to use.
RNG_SEED = 42
rng = np.random.default_rng(RNG_SEED)

# global pool of possible structural-system categories (from ground truth)
_gt_categories = sorted({
    str(v)
    for area_gdf in area_gdfs.values()
    for v in area_gdf["ground_truth_structural_system"]
    if not (v is None or (isinstance(v, float) and np.isnan(v)))
})

def _random_other_category(true_val, categories, rng):
    others = [c for c in categories if c != str(true_val)]
    if not others:
        return true_val
    return rng.choice(others)

for area, area_gdf in area_gdfs.items():
    gt = area_gdf["ground_truth_structural_system"]
    n = len(area_gdf)
    for model_name in MODEL_FILES:
        pred_col = f"{model_name}_structural_system"
        flip_mask = rng.random(n) < 0.20  # ~20% wrong

        preds = []
        for is_wrong, g in zip(flip_mask, gt):
            if g is None or (isinstance(g, float) and np.isnan(g)):
                preds.append(None)
            elif is_wrong:
                preds.append(_random_other_category(g, _gt_categories, rng))
            else:
                preds.append(g)
        area_gdf[pred_col] = preds
    area_gdfs[area] = area_gdf
    print(f"Area '{area}': generated synthetic predictions for {list(MODEL_FILES.keys())}")

# ─────────────────────────────────────────
# 4) ERROR COLUMNS: {model}_error = (prediction == ground_truth)
#    None if either side is None
# ─────────────────────────────────────────
for area, area_gdf in area_gdfs.items():
    gt = area_gdf["ground_truth_structural_system"]
    for model_name in MODEL_FILES:
        pred_col  = f"{model_name}_structural_system"
        error_col = f"{model_name}_error"
        pred = area_gdf[pred_col]

        def compare(g, p):
            if g is None or p is None:
                return None
            # treat NaN (float) as missing too
            if isinstance(g, float) and np.isnan(g):
                return None
            if isinstance(p, float) and np.isnan(p):
                return None
            return bool(g == p)

        area_gdf[error_col] = [compare(g, p) for g, p in zip(gt, pred)]

# ─────────────────────────────────────────
# 5) BUILD GLOBAL COLOR MAP FOR STRUCTURAL-SYSTEM CATEGORIES
#    (shared across ground_truth + all model prediction columns)
# ─────────────────────────────────────────
STRUCT_COLS = ["ground_truth_structural_system"] + [f"{m}_structural_system" for m in MODEL_FILES]
ERROR_COLS  = [f"{m}_error" for m in MODEL_FILES]
ALL_COLUMNS = ["ground_truth_structural_system"]
for m in MODEL_FILES:
    ALL_COLUMNS.append(f"{m}_structural_system")
    ALL_COLUMNS.append(f"{m}_error")

def is_missing(v):
    if v is None:
        return True
    if isinstance(v, float) and np.isnan(v):
        return True
    return False

categories = set()
for area_gdf in area_gdfs.values():
    for col in STRUCT_COLS:
        if col in area_gdf.columns:
            for v in area_gdf[col]:
                if not is_missing(v):
                    categories.add(str(v))

categories = sorted(categories)

def hsl_to_hex(h, s, l):
    h = h % 360
    s /= 100.0
    l /= 100.0
    c = (1 - abs(2 * l - 1)) * s
    x = c * (1 - abs((h / 60.0) % 2 - 1))
    m = l - c / 2
    if   h < 60:  r, g, b = c, x, 0
    elif h < 120: r, g, b = x, c, 0
    elif h < 180: r, g, b = 0, c, x
    elif h < 240: r, g, b = 0, x, c
    elif h < 300: r, g, b = x, 0, c
    else:         r, g, b = c, 0, x
    R, G, B = [int(round((v + m) * 255)) for v in (r, g, b)]
    return "#{:02x}{:02x}{:02x}".format(R, G, B)

# Deterministic, non-repeating colors via golden-angle hue stepping
GOLDEN_ANGLE = 137.508
CATEGORY_COLORS = {
    cat: hsl_to_hex((i * GOLDEN_ANGLE) % 360, 65, 50)
    for i, cat in enumerate(categories)
}
print(f"Structural system categories ({len(categories)}): {categories}")

# ─────────────────────────────────────────
# 6) BUILD GEOJSON PER AREA (only relevant columns + geometry, in EPSG:4326)
# ─────────────────────────────────────────
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

geojson_data = {}
area_centers = {}

for area, area_gdf in area_gdfs.items():
    gdf4326 = area_gdf.to_crs(4326)

    keep_cols = [c for c in ALL_COLUMNS if c in gdf4326.columns]
    features = []
    for _, row in gdf4326.iterrows():
        geom = row.geometry
        if geom is None or geom.is_empty:
            continue
        props = {c: clean(row[c]) for c in keep_cols}
        features.append({
            "type": "Feature",
            "geometry": geom.__geo_interface__,
            "properties": props,
        })

    geojson_data[area] = {"type": "FeatureCollection", "features": features}

    b = gdf4326.total_bounds  # [minx, miny, maxx, maxy]
    area_centers[area] = ((b[1] + b[3]) / 2, (b[0] + b[2]) / 2)

all_centers = list(area_centers.values())
g_lat = sum(c[0] for c in all_centers) / len(all_centers)
g_lon = sum(c[1] for c in all_centers) / len(all_centers)

# ─────────────────────────────────────────
# 7) BUILD MAP
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
# COLUMN CONFIG (structural-system vs error) for JS
# ─────────────────────────────────────────
COLUMN_CONFIG = {}
COLUMN_CONFIG["ground_truth_structural_system"] = {"type": "structural", "label": "Ground truth structural system"}
for m_name in MODEL_FILES:
    COLUMN_CONFIG[f"{m_name}_structural_system"] = {"type": "structural", "label": f"{m_name} – predicted structural system"}
    COLUMN_CONFIG[f"{m_name}_error"]             = {"type": "error",      "label": f"{m_name} – correct?"}

# ─────────────────────────────────────────
# EMBED DATA AS JS
# ─────────────────────────────────────────
js_lines = ["<script>"]
js_lines.append("var AREA_DATA = " + json.dumps(geojson_data) + ";")
js_lines.append("var AREA_CENTERS = " + json.dumps(
    {a: {"lat": v[0], "lon": v[1]} for a, v in area_centers.items()}
) + ";")
js_lines.append("var COLUMN_CONFIG = " + json.dumps(COLUMN_CONFIG) + ";")
js_lines.append("var CATEGORY_COLORS = " + json.dumps(CATEGORY_COLORS) + ";")
js_lines.append("var AREAS = " + json.dumps(list(AREA_FILES.keys())) + ";")
js_lines.append(f'var COLOR_GREEN = "{GREEN}";')
js_lines.append(f'var COLOR_RED = "{RED}";')
js_lines.append("</script>")
m.get_root().html.add_child(folium.Element("\n".join(js_lines)))

# ─────────────────────────────────────────
# DROPDOWN UI
# ─────────────────────────────────────────
area_options = "\n".join(f'      <option value="{a}">{a}</option>' for a in AREA_FILES.keys())
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
    <label style="font-weight:bold;display:block;margin-bottom:5px;">Area</label>
    <select id="areaSelect" style="width:160px;font-size:13px;padding:4px 6px;">
{area_options}
    </select>
  </div>
  <div>
    <label style="font-weight:bold;display:block;margin-bottom:5px;">Layer / column</label>
    <select id="columnSelect" style="width:300px;font-size:13px;padding:4px 6px;">
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
    box-shadow:0 2px 10px rgba(0,0,0,.15); min-width:200px; max-height:50vh; overflow-y:auto;">
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

  function getLeafletMap() {
    var keys = Object.keys(window).filter(function(k){ return k.startsWith('map_'); });
    return keys.length ? window[keys[0]] : null;
  }

  // --- Color helpers ---------------------------------------------------

  function getStructColor(value) {
    if (value === null || value === undefined) return null; // -> transparent
    return CATEGORY_COLORS[String(value)] || "#999999";
  }

  function getErrorColor(value) {
    if (value === null || value === undefined) return null; // -> transparent
    return value ? COLOR_GREEN : COLOR_RED;
  }

  function styleFeature(col, cfg) {
    return function(feature) {
      var v = feature.properties[col];
      var color;
      if (cfg.type === "structural") {
        color = getStructColor(v);
      } else { // error
        color = getErrorColor(v);
      }
      if (color === null) {
        return { fillColor: "#000000", fillOpacity: 0, color: "#222222", weight: 1, opacity: 0.4 };
      }
      return { fillColor: color, fillOpacity: 0.75, color: "#222222", weight: 1, opacity: 0.6 };
    };
  }

  // --- Legend ------------------------------------------------------------

  function buildLegend(area, col, cfg) {
    var title = document.getElementById('legend-title');
    var body  = document.getElementById('legend-body');
    title.innerText = cfg.label || col;
    body.innerHTML = "";

    if (cfg.type === "error") {
      [["True (correct)", COLOR_GREEN], ["False (incorrect)", COLOR_RED], ["No data", null]].forEach(function(pair) {
        var label = pair[0], color = pair[1];
        var swatch = (color === null)
          ? 'border:1px dashed #999;background:white;'
          : 'border:1px solid #555;background:' + color + ';';
        body.innerHTML +=
          '<div style="display:flex;align-items:center;margin-top:4px;">' +
          '<div style="width:14px;height:14px;' + swatch + 'margin-right:6px;"></div>' +
          '<span>' + label + '</span></div>';
      });
      return;
    }

    // structural: list categories actually present in this area for this column,
    // using the GLOBAL shared color map so colors stay consistent across columns
    var data = AREA_DATA[area];
    var seen = {};
    var order = [];
    var hasNone = false;
    if (data) {
      data.features.forEach(function(f) {
        var v = f.properties[col];
        if (v === null || v === undefined) { hasNone = true; return; }
        var key = String(v);
        if (!(key in seen)) { seen[key] = true; order.push(key); }
      });
    }
    order.sort();
    order.forEach(function(key) {
      var color = CATEGORY_COLORS[key] || "#999999";
      body.innerHTML +=
        '<div style="display:flex;align-items:center;margin-top:4px;">' +
        '<div style="width:14px;height:14px;background:' + color + ';border:1px solid #555;margin-right:6px;"></div>' +
        '<span>' + key + '</span></div>';
    });
    if (hasNone) {
      body.innerHTML +=
        '<div style="display:flex;align-items:center;margin-top:4px;">' +
        '<div style="width:14px;height:14px;border:1px dashed #999;background:white;margin-right:6px;"></div>' +
        '<span>No data</span></div>';
    }
    if (order.length === 0 && !hasNone) {
      body.innerHTML = '<i>No data</i>';
    }
  }

  // --- Tooltip field list --------------------------------------------------

  function tooltipFields(col) {
    var base = ["ground_truth_structural_system"];
    if (base.indexOf(col) === -1) base.push(col);
    return base;
  }

  // --- Update map ----------------------------------------------------------

  function updateMap() {
    var lmap = getLeafletMap();
    if (!lmap) { setTimeout(updateMap, 300); return; }

    var area = document.getElementById('areaSelect').value;
    var col  = document.getElementById('columnSelect').value;
    var cfg  = COLUMN_CONFIG[col];

    if (currentLayer) { lmap.removeLayer(currentLayer); currentLayer = null; }

    var data = AREA_DATA[area];
    if (data && data.features && data.features.length > 0) {
      var fields = tooltipFields(col).filter(function(f) {
        return data.features[0].properties.hasOwnProperty(f);
      });
      currentLayer = L.geoJSON(data, {
        style: styleFeature(col, cfg),
        onEachFeature: function(feature, layer) {
          var rows = fields.map(function(f) {
            var v = feature.properties[f];
            return '<b>' + f + '</b>: ' + (v === null || v === undefined ? '-' : v);
          }).join('<br>');
          layer.bindTooltip(rows, {sticky: true});
        }
      }).addTo(lmap);
    }

    buildLegend(area, col, cfg);

    var c = AREA_CENTERS[area];
    if (c) lmap.setView([c.lat, c.lon], 16);
  }

  function init() {
    var lmap = getLeafletMap();
    if (!lmap) { setTimeout(init, 300); return; }
    document.getElementById('areaSelect').addEventListener('change', updateMap);
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
out = "/home/miguel/Documents/UNI/Master/2/TFM/presentation/maps/ml_results_map.html"
m.save(out)
print(f"\n✓ Saved → {out}")