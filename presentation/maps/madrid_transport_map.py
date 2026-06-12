"""
madrid_transport_map.py
Run this script locally (where folium + geopandas are installed) to generate
madrid_transport_map.html

Usage:
    pip install folium geopandas shapely
    python madrid_transport_map.py
"""

import folium
import geopandas as gpd
import json
import os
from shapely.ops import unary_union

# ─────────────────────────────────────────
# CONFIGURATION  ← edit these
# ─────────────────────────────────────────
BASE_DIR = "/home/miguel/Documents/UNI/Master/2/TFM/presentation/maps/vector/MadridTransport"

# Only these areas will be loaded and offered in the dropdown
# Use the exact suffix that appears in the filenames (underscores)
PLACE_LIST = ["SAN_DIEGO"] #["ARCOS", "SAN_DIEGO", "CUATRO_CAMINOS"]

# Display labels shown in the dropdown (same order as PLACE_LIST)
PLACE_DISPLAY = {
    "ARCOS":         "Arcos",
    "SAN_DIEGO":     "San Diego",
    "CUATRO_CAMINOS":"Cuatro Caminos",
    "GAZTAMBIDE":    "Gaztambide",
    "PILAR":         "Pilar",
}

# Real WMS endpoints extracted from the GetCapabilities URLs in the service metadata XML.
# The geoportal.madrid.es URLs are metadata catalogue pages, not WMS endpoints.
# 2023: confirmed working with layer "raster"
WMS_2023 = "https://servpub.madrid.es/georaster/ORTOFOTOS_COMPLETAS/ORTO_2023_10_10/ows"
# 2001: the ORTO_2001_10_10 path returns empty — try the metadata catalogue endpoint
# which redirects to the real OWS. If tiles are still blank, fetch:
#   curl "https://geoportal.madrid.es/IDEAM_WBGEOPORTAL/wms?id=SPA_28079_SERVICIO_ORTOFOTO_2001_10_VC&service=WMS&version=1.3.0&request=GetCapabilities" | grep -o '<Name>[^<]*</Name>'
# and update WMS_2001 + WMS_LAYER_2001 accordingly.
WMS_2001 = "https://servpub.madrid.es/georaster/ORTOFOTOS_COMPLETAS/ORTO_2001_E8000_10_10/ows"
WMS_LAYER_2023 = "ORTO_2023_10_10"
WMS_LAYER_2001 = "ORTO_2001_E8000_10_10"  # matches the service path pattern

LABEL_COLORS = {
    1: "#8B4513",   # brown        – Building
    2: "#404040",   # dark grey    – Road
    3: "#FF8C00",   # orange       – Sidewalk
    4: "#00008B",   # dark blue    – Swimming Pool
    5: "#FF6B6B",   # light red    – Bike Lane
    6: "#ADD8E6",   # light blue   – Parking
}
LABEL_NAMES = {
    1: "Building", 2: "Road", 3: "Sidewalk",
    4: "Swimming Pool", 5: "Bike Lane", 6: "Parking",
}

# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────
def load_gpkg(path):
    try:
        gdf = gpd.read_file(path).to_crs(4326)
        print(f"  Loaded {os.path.basename(path)}  ({len(gdf)} features)")
        return gdf
    except Exception as e:
        print(f"  WARN: could not load {os.path.basename(path)}: {e}")
        return None

def dissolve_by_label(gdf):
    """Dissolve all polygons that share the same label into a single
    (possibly multi-part) geometry.  Returns a GeoDataFrame with one
    row per label value."""
    dissolved = (
        gdf[["label", "geometry"]]
        .groupby("label", as_index=False)
        .agg(geometry=("geometry", unary_union))
    )
    return gpd.GeoDataFrame(dissolved, geometry="geometry", crs=gdf.crs)

def gdf_to_geojson(gdf):
    """Convert GeoDataFrame to a plain dict GeoJSON.
    Works for both dissolved (one row/label) and raw (many rows) frames."""
    features = []
    for _, row in gdf.iterrows():
        label = int(row["label"]) if row.get("label") is not None else 1
        geom  = row.geometry
        if geom is None or geom.is_empty:
            continue
        features.append({
            "type": "Feature",
            "geometry": geom.__geo_interface__,
            "properties": {"label": label},
        })
    return {"type": "FeatureCollection", "features": features}

# ─────────────────────────────────────────
# LOAD DATA  (only PLACE_LIST areas)
# ─────────────────────────────────────────
layers_data = {}   # (mode, area) -> geojson dict | None
area_bounds = {}   # area -> (center_lat, center_lon)

for area in PLACE_LIST:
    print(f"\n── {area} ──")
    for mode, fname in [
        ("GT",   f"MadridStreet_2023_GT_{area}.gpkg"),
        ("2001", f"MadridStreet_2001_{area}.gpkg"),
        ("2023", f"MadridStreet_2023_{area}.gpkg"),
    ]:
        fpath = os.path.join(BASE_DIR, fname)
        gdf   = load_gpkg(fpath)

        if gdf is not None and len(gdf) > 0:
            # Compute centroid FIRST, from the raw loaded data before any
            # dissolve / simplification that could shrink or empty geometries
            if area not in area_bounds:
                b = gdf.total_bounds   # [minx, miny, maxx, maxy]
                area_bounds[area] = ((b[1]+b[3])/2, (b[0]+b[2])/2)

            # GT layers: dissolve by label to merge adjacent same-class polygons
            if mode == "GT":
                print(f"    → dissolving GT by label …", end=" ")
                gdf = dissolve_by_label(gdf)
                print(f"{len(gdf)} dissolved features")

            # Optional: gentle simplification to reduce file size.
            # 0.5 m in UTM is barely visible at zoom 17 but cuts vertex count.
            # Remove these four lines if you want pixel-perfect geometry.
            utm_crs = gdf.estimate_utm_crs()
            gdf = gdf.to_crs(utm_crs)
            gdf = gdf.copy()
            gdf.geometry = gdf.geometry.simplify(0.5, preserve_topology=True)
            gdf = gdf[~gdf.geometry.is_empty & gdf.geometry.notna()].copy()
            gdf = gdf.to_crs(4326)

            layers_data[(mode, area)] = gdf_to_geojson(gdf)
        else:
            layers_data[(mode, area)] = None

# Global initial map centre (average of all area centroids)
all_centers = list(area_bounds.values())
global_lat  = sum(c[0] for c in all_centers) / max(len(all_centers), 1)
global_lon  = sum(c[1] for c in all_centers) / max(len(all_centers), 1)

# ─────────────────────────────────────────
# BUILD FOLIUM MAP
# ─────────────────────────────────────────
m = folium.Map(location=[global_lat, global_lon], zoom_start=15,
               tiles=None, max_zoom=22, control_scale=True)

folium.TileLayer(
    tiles="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
    name="CartoDB Positron",
    attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/">CARTO</a>',
    overlay=False, control=True,
    max_zoom=22, max_native_zoom=19, show=True,
    subdomains="abcd",
).add_to(m)

folium.WmsTileLayer(
    url=WMS_2001, name="Madrid 2001 (Ortofoto)",
    layers=WMS_LAYER_2001, fmt="image/jpeg", transparent=False,
    overlay=False, control=True,
    max_zoom=22, max_native_zoom=19, show=False,
    attr="Geoportal Madrid – Ortofoto 2001",
    version="1.3.0",
).add_to(m)

folium.WmsTileLayer(
    url=WMS_2023, name="Madrid 2023 (Ortofoto)",
    layers=WMS_LAYER_2023, fmt="image/jpeg", transparent=False,
    overlay=False, control=True,
    max_zoom=22, max_native_zoom=19, show=False,
    attr="Geoportal Madrid – Ortofoto 2023",
    version="1.3.0",
).add_to(m)

folium.LayerControl(collapsed=False, position="topright").add_to(m)

# ─────────────────────────────────────────
# EMBED GEOJSON + BOUNDS AS JS VARIABLES
# ─────────────────────────────────────────
js_lines = ["<script>", "var GPKG_DATA = {};", "var AREA_BOUNDS = {};"]

for (mode, area), geojson in layers_data.items():
    key     = f"{mode}_{area}"
    payload = json.dumps(geojson) if geojson else "null"
    js_lines.append(f'GPKG_DATA["{key}"] = {payload};')

for area, (clat, clon) in area_bounds.items():
    js_lines.append(f'AREA_BOUNDS["{area}"] = {{lat:{clat:.6f}, lon:{clon:.6f}}};')

js_lines.append("</script>")
m.get_root().html.add_child(folium.Element("\n".join(js_lines)))

# ─────────────────────────────────────────
# DROPDOWN UI  (built dynamically from PLACE_LIST)
# ─────────────────────────────────────────
area_options = "\n".join(
    f'      <option value="{a}">{PLACE_DISPLAY.get(a, a)}</option>'
    for a in PLACE_LIST
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
    <label style="font-weight:bold;display:block;margin-bottom:5px;">Model</label>
    <select id="modelSelect" style="width:150px;font-size:13px;padding:4px 6px;">
      <option value="GT">Ground Truth</option>
      <option value="2001">Model 2001</option>
      <option value="2023">Model 2023</option>
    </select>
  </div>
  <div>
    <label style="font-weight:bold;display:block;margin-bottom:5px;">Area</label>
    <select id="areaSelect" style="width:170px;font-size:13px;padding:4px 6px;">
{area_options}
    </select>
  </div>
</div>
"""
m.get_root().html.add_child(folium.Element(dropdown_html))

# ─────────────────────────────────────────
# LEGEND (always visible)
# ─────────────────────────────────────────
legend_items = ""
for lid, lname in LABEL_NAMES.items():
    c = LABEL_COLORS[lid]
    legend_items += f"""
    <div style="display:flex;align-items:center;margin-top:6px;">
      <div style="width:16px;height:16px;background:{c};margin-right:8px;
                  border-radius:3px;flex-shrink:0;"></div>
      <span>{lid} – {lname}</span>
    </div>"""

legend_html = f"""
<div id="map-legend" style="
    position:fixed; bottom:40px; left:15px; z-index:9999;
    background:white; padding:12px 16px;
    border:1px solid #bbb; border-radius:10px;
    font-family:sans-serif; font-size:13px;
    box-shadow:0 2px 10px rgba(0,0,0,.15); min-width:175px;">
  <b style="font-size:14px;">Legend</b>
  {legend_items}
</div>
"""
m.get_root().html.add_child(folium.Element(legend_html))

# ─────────────────────────────────────────
# MAIN JS INTERACTION LOGIC
# ─────────────────────────────────────────
main_js = """
<script>
(function() {
  var MODEL_TO_BG = {
    "GT":   "Madrid 2023 (Ortofoto)",
    "2001": "Madrid 2001 (Ortofoto)",
    "2023": "Madrid 2023 (Ortofoto)"
  };

  var LABEL_COLORS_JS = {
    1: "#8B4513", 2: "#404040", 3: "#FF8C00",
    4: "#00008B", 5: "#FF6B6B", 6: "#ADD8E6"
  };

  var currentLayer = null;

  function getLeafletMap() {
    var keys = Object.keys(window).filter(function(k){ return k.startsWith('map_'); });
    return keys.length ? window[keys[0]] : null;
  }

  function activateBackground(bgName) {
    document.querySelectorAll('.leaflet-control-layers-base label').forEach(function(lbl) {
      var txt = lbl.innerText.trim();
      var inp = lbl.querySelector('input[type=radio]');
      if (inp && txt === bgName && !inp.checked) inp.click();
    });
  }

  function styleFeature(feature) {
    var color = LABEL_COLORS_JS[feature.properties.label] || "#888888";
    return { fillColor: color, fillOpacity: 0.8, color: "none", weight: 0 };
  }

  function updateMap() {
    var lmap = getLeafletMap();
    if (!lmap) { setTimeout(updateMap, 500); return; }

    var model = document.getElementById('modelSelect').value;
    var area  = document.getElementById('areaSelect').value;
    var key   = model + "_" + area;

    // Remove previous vector layer
    if (currentLayer) { lmap.removeLayer(currentLayer); currentLayer = null; }

    // Add new vector layer (no hover, no popup, no border)
    var data = GPKG_DATA[key];
    if (data && data.features && data.features.length > 0) {
      currentLayer = L.geoJSON(data, {
        style: styleFeature,
        interactive: false
      }).addTo(lmap);
    }

    // Switch background to the appropriate WMS / OSM
    var bgName = MODEL_TO_BG[model] || "OpenStreetMap";
    activateBackground(bgName);

    // Fly/zoom to area centroid
    var b = AREA_BOUNDS[area];
    if (b) lmap.setView([b.lat, b.lon], 17);
  }

  function init() {
    var lmap = getLeafletMap();
    if (!lmap) { setTimeout(init, 500); return; }

    document.getElementById('modelSelect').addEventListener('change', updateMap);
    document.getElementById('areaSelect').addEventListener('change', updateMap);

    // Unlock overzoom without re-requesting WMS tiles
    lmap.setMaxZoom(22);
    lmap.eachLayer(function(layer) {
      if (layer.options && layer.options.maxNativeZoom !== undefined) {
        layer.options.maxZoom = 22;
      }
    });

    updateMap();  // initial render
  }

  setTimeout(init, 1200);
})();
</script>
"""
m.get_root().html.add_child(folium.Element(main_js))

# ─────────────────────────────────────────
# SAVE
# ─────────────────────────────────────────
out = "/home/miguel/Documents/UNI/Master/2/TFM/presentation/maps/madrid_transport_map.html"
m.save(out)
print(f"\n✓ Saved → {out}")