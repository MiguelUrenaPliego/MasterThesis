import folium
import rasterio
import numpy as np
import json
import geopandas as gpd
import pandas as pd
import branca.colormap as bcm
from matplotlib import colormaps
from folium.raster_layers import ImageOverlay
from rasterio.warp import reproject, Resampling, transform_bounds
from rasterio.crs import CRS
import base64
from io import BytesIO
from PIL import Image

# ─────────────────────────────────────────
# INPUTS
# ─────────────────────────────────────────
sentinel2_url = "https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2024_3857/default/g/{z}/{y}/{x}.jpg"
google_hybrid  = "https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}"

dtm_path       = "/home/miguel/Documents/UNI/Master/2/TFM/presentation/maps/images/dtm.tif"
dsm_path       = "/home/miguel/Documents/UNI/Master/2/TFM/presentation/maps/images/dsm_very_low_res.tif"
year_path      = "/home/miguel/Documents/UNI/Master/2/TFM/presentation/maps/images/year.tif"
roofs_path     = "/home/miguel/Documents/UNI/Master/2/TFM/presentation/maps/images/roofs.tif"
drone_rgb_path = "/home/miguel/Documents/UNI/Master/2/TFM/presentation/maps/images/image_very_low_res.tif"
drone_hr_path  = "/home/miguel/Documents/UNI/Master/2/TFM/presentation/maps/images/image_max_res_tile.tif"

santo_domingo_path = "/home/miguel/Documents/UNI/Master/2/TFM/presentation/maps/vector/santo_domingo_pilot_region.gpkg"
santo_domingo = gpd.read_file(santo_domingo_path)
santo_domingo = santo_domingo.rename(columns={"height":"height_survey"})
santo_domingo_height_path = "/home/miguel/Documents/UNI/Master/2/TFM/presentation/maps/vector/santo_domingo_heights.gpkg"
santo_domingo_h = gpd.read_file(santo_domingo_height_path)
santo_domingo_h["geometry"] = santo_domingo_h.geometry.centroid
santo_domingo_h = santo_domingo_h.rename(columns={"street_hei":"street_height","building_h":"height"})
# assign height to santo_domingo based on nearest centroid from santo_domingo_h
santo_domingo = gpd.sjoin_nearest(
    santo_domingo,
    santo_domingo_h[["geometry", "height", "street_height"]],
    how="left",
    distance_col="dist"
)
santo_domingo["height_error"] = santo_domingo["height_survey"] - santo_domingo["height"]
santo_domingo["height_error_abs"] = santo_domingo["height_error"].abs()

# colourmaps — all thematic layers use Blues (light→dark, linear)
CMAP_ELEV   = colormaps["Blues"]   # DTM / DSM / Height / street_height
CMAP_YEAR   = colormaps["Blues"]   # Year
CMAP_ERR    = colormaps["RdYlGn_r"]     # height_error_abs (green=small, red=large)
ROOF_COLORS = ["#e41a1c", "#377eb8", "#4daf4a", "#ff7f00"]   # 4 classes

# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────

def normalize(a, vmin, vmax):
    a = np.nan_to_num(a, nan=vmin)
    return np.clip((a - vmin) / (vmax - vmin + 1e-9), 0, 1)

def apply_nodata(arr, nodata):
    arr = arr.astype(float)
    if nodata is not None:
        arr[arr == nodata] = np.nan
    return arr

def read_raster(path, name):
    with rasterio.open(path) as src:
        arr  = src.read().astype(float)
        nd   = src.nodata
        t    = src.transform
        crs  = src.crs
        bounds = src.bounds
        # convert bounds to WGS-84
        bnds_4326 = transform_bounds(crs, CRS.from_epsg(4326), *bounds)
        if nd is not None:
            arr[arr == nd] = np.nan
        if arr.shape[0] == 1:
            arr = arr[0]
        print(f"[{name}] shape={arr.shape}  nodata={nd}")
        return arr, t, crs, bounds, bnds_4326

def read_rgb(path, name):
    with rasterio.open(path) as src:
        cnt = src.count
        bands = [1, 2, 3] if cnt >= 3 else [1, 1, 1]
        arr = src.read(bands).astype(float)
        nd  = src.nodata
        bounds = src.bounds
        crs    = src.crs
        bnds_4326 = transform_bounds(crs, CRS.from_epsg(4326), *bounds)

        # Build nodata mask BEFORE stretching
        if nd is not None:
            nodata_mask = np.any(arr == nd, axis=0)
        else:
            # Treat pixels where ALL bands are 0 as nodata (common in drone GeoTIFFs)
            nodata_mask = np.all(arr == 0, axis=0)

        arr_out = np.zeros_like(arr)
        for i in range(3):
            ch = arr[i].copy()
            ch[nodata_mask] = np.nan
            lo = np.nanpercentile(ch, 2)
            hi = np.nanpercentile(ch, 98)
            arr_out[i] = np.clip((ch - lo) / (hi - lo + 1e-9), 0, 1) * 255

        rgb = np.moveaxis(arr_out, 0, -1).astype(np.uint8)
        alpha = np.where(nodata_mask, 0, 200).astype(np.uint8)
        rgba  = np.dstack([rgb, alpha])

        print(f"[{name}] RGB shape={rgb.shape}  nodata_pixels={nodata_mask.sum()}")
        return rgba, bnds_4326   # returns RGBA directly

def compute_height(dsm, dtm_aligned):
    mask = np.isnan(dsm) | np.isnan(dtm_aligned)
    h    = dsm - dtm_aligned
    h[mask] = np.nan
    return h

def to_rgba(arr, vmin, vmax, cmap):
    norm = normalize(arr, vmin, vmax)
    rgba = (cmap(norm) * 255).astype(np.uint8)
    rgba[np.isnan(arr), 3] = 0
    rgba[~np.isnan(arr), 3] = 200      # slight transparency baked in
    return rgba

def ndarray_to_png_b64(rgba):
    img = Image.fromarray(rgba, "RGBA")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

def multispectral_to_rgb(arr):
    """Pick bands 4,3,2 (index 3,2,1) as R,G,B if available."""
    bands, h, w = arr.shape
    if bands >= 4:
        r, g, b = arr[3], arr[2], arr[1]
    elif bands >= 3:
        r, g, b = arr[0], arr[1], arr[2]
    else:
        r = g = b = arr[0]
    rgb = np.stack([r, g, b], axis=-1).astype(float)
    for i in range(3):
        lo, hi = np.nanpercentile(rgb[:, :, i], 2), np.nanpercentile(rgb[:, :, i], 98)
        rgb[:, :, i] = np.clip((rgb[:, :, i] - lo) / (hi - lo + 1e-9), 0, 1) * 255
    return rgb.astype(np.uint8)

# ─────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────
dsm_arr,  dsm_t,  dsm_crs,  dsm_bounds,  dsm_4326  = read_raster(dsm_path,  "DSM")
dtm_arr,  dtm_t,  dtm_crs,  dtm_bounds,  dtm_4326  = read_raster(dtm_path,  "DTM")
year_arr, year_t, year_crs, year_bounds, year_4326  = read_raster(year_path, "YEAR")
roofs_arr, roofs_t, roofs_crs, roofs_bounds, roofs_4326 = read_raster(roofs_path, "ROOFS")

drone_low_rgba, drone_low_4326 = read_rgb(drone_rgb_path, "DRONE LOW")
drone_hr_rgba,  drone_hr_4326  = read_rgb(drone_hr_path,  "DRONE HIGH")

# ─────────────────────────────────────────
# ALIGN DTM TO DSM GRID
# ─────────────────────────────────────────
dtm_aligned = np.zeros_like(dsm_arr)
reproject(
    source=dtm_arr,
    destination=dtm_aligned,
    src_transform=dtm_t,
    src_crs=dtm_crs,
    dst_transform=dsm_t,
    dst_crs=dsm_crs,
    resampling=Resampling.bilinear
)
dtm_aligned[dtm_aligned == 0] = np.nan   # treat reprojeced zeros as nodata

# ─────────────────────────────────────────
# HEIGHT
# ─────────────────────────────────────────
height_arr = compute_height(dsm_arr, dtm_aligned)

# ─────────────────────────────────────────
# YEAR CLEAN
# ─────────────────────────────────────────
year_arr[year_arr == 0] = np.nan

# ─────────────────────────────────────────
# ROOFS → RGB
# ─────────────────────────────────────────
roofs_rgb_arr = multispectral_to_rgb(roofs_arr)

# ─────────────────────────────────────────
# COLOUR RANGES
# ─────────────────────────────────────────
# Full linear range (min→max) for all thematic colormaps
vmin_elev = float(np.nanmin(np.concatenate([dsm_arr[~np.isnan(dsm_arr)], dtm_aligned[~np.isnan(dtm_aligned)]])))
vmax_elev = float(np.nanmax(np.concatenate([dsm_arr[~np.isnan(dsm_arr)], dtm_aligned[~np.isnan(dtm_aligned)]])))

vmin_h  = 3 #float(np.nanmin(height_arr[~np.isnan(height_arr)]))
vmax_h  = 30 #float(np.nanmax(height_arr[~np.isnan(height_arr)]))

vmin_yr = 1975
vmax_yr = 2015

# ── LEGEND DISPLAY RANGES ──────────────────────────────────────────────
# These control ONLY the numbers printed under the legend gradient bars.
# They are independent from vmin_elev/vmax_elev/vmin_h/vmax_h/vmin_yr/vmax_yr
# above, which control how raster values are mapped to colors (to_rgba) and
# how vector features are colored (hex_color_from_cmap).
# Edit these freely if you want the legend to show a different range than
# what's actually used for coloring (e.g. a "nicer" rounded range).
legend_vmin_elev, legend_vmax_elev = vmin_elev, vmax_elev
legend_vmin_h,    legend_vmax_h    = vmin_h,    vmax_h
legend_vmin_yr,   legend_vmax_yr   = vmin_yr,   vmax_yr

# street_height range for DSM/DTM vector companion
_sh_col = "street_height" if "street_height" in santo_domingo.columns else "height"
vmin_sh = float(santo_domingo[_sh_col].dropna().min())
vmax_sh = float(santo_domingo[_sh_col].dropna().max())

# Legend display range for street height (independent of vmin_sh/vmax_sh,
# which are used to color the "Buildings – DSM/DTM" features)
legend_vmin_sh, legend_vmax_sh = legend_vmin_elev, legend_vmax_elev

# height_error: coloring range (used by style_err) and legend display range
# (independent — edit legend_vmin_err/legend_vmax_err to change just the
# numbers shown on the legend bar)
_err_col = "height_error_abs" if "height_error_abs" in santo_domingo.columns else "height_error"
vmin_err = 0#float(santo_domingo[_err_col].dropna().min())
vmax_err = 10#float(santo_domingo[_err_col].dropna().max())
legend_vmin_err, legend_vmax_err = vmin_err, vmax_err

# ─────────────────────────────────────────
# BUILD RGBA + encode PNG
# ─────────────────────────────────────────
dsm_rgba    = to_rgba(dsm_arr,     vmin_elev, vmax_elev, CMAP_ELEV)
# Use the ORIGINAL (full-extent) DTM array + bounds for display, not the
# DSM-grid-aligned version (which is cropped to the DSM's smaller extent).
dtm_rgba    = to_rgba(dtm_arr,     vmin_elev, vmax_elev, CMAP_ELEV)
height_rgba = to_rgba(height_arr,  vmin_h,    vmax_h,    CMAP_ELEV)
year_rgba   = to_rgba(year_arr,    vmin_yr,   vmax_yr,   CMAP_YEAR)

def rgb_to_rgba_png(rgb):
    """For multispectral RGB arrays (no nodata mask available - use 200 alpha)."""
    alpha = np.full(rgb.shape[:2], 200, dtype=np.uint8)
    rgba  = np.dstack([rgb, alpha])
    return ndarray_to_png_b64(rgba)

dsm_png    = ndarray_to_png_b64(dsm_rgba)
dtm_png    = ndarray_to_png_b64(dtm_rgba)
height_png = ndarray_to_png_b64(height_rgba)
year_png   = ndarray_to_png_b64(year_rgba)
roofs_png  = rgb_to_rgba_png(roofs_rgb_arr)
drone_low_png = ndarray_to_png_b64(drone_low_rgba)
drone_hr_png  = ndarray_to_png_b64(drone_hr_rgba)

# ─────────────────────────────────────────
# RASTER NUMPY ARRAYS (for click popup)
# ─────────────────────────────────────────
# Store as JSON arrays for use in JS (downsampled for size)
def arr_to_js_json(arr, max_size=200):
    """Downsample 2D array and return JSON string."""
    h, w = arr.shape
    sy = max(1, h // max_size)
    sx = max(1, w // max_size)
    a  = arr[::sy, ::sx]
    return json.dumps(np.where(np.isnan(a), None, np.round(a.astype(float), 2)).tolist())

dsm_js    = arr_to_js_json(dsm_arr)
dtm_js    = arr_to_js_json(dtm_arr)
height_js = arr_to_js_json(height_arr)
year_js   = arr_to_js_json(year_arr)

# ─────────────────────────────────────────
# MAP
# ─────────────────────────────────────────
center = (
    santo_domingo.to_crs(4326).union_all().centroid.y,
    santo_domingo.to_crs(4326).union_all().centroid.x,
)

m = folium.Map(location=center, zoom_start=14, tiles=None, max_zoom=22)

# ── Background base layers ──
folium.TileLayer(sentinel2_url, name="Sentinel-2 (background)", attr="EOX",
                 overlay=False, control=True, max_zoom=22, max_native_zoom=18).add_to(m)
folium.TileLayer(google_hybrid,  name="Google Hybrid (background)", attr="Google",
                 overlay=False, control=True, max_zoom=22, max_native_zoom=20).add_to(m)

# ── Helper: add raster overlay into a FeatureGroup ──
def add_raster_fg(png_b64, bounds_4326, name, show=False):
    """bounds_4326: (left, bottom, right, top)"""
    fg = folium.FeatureGroup(name=name, overlay=True, show=show)
    folium.raster_layers.ImageOverlay(
        image=png_b64,
        bounds=[[bounds_4326[1], bounds_4326[0]],
                [bounds_4326[3], bounds_4326[2]]],
        opacity=1.0,   # alpha already baked into RGBA
        origin="upper",
        zindex=400,
    ).add_to(fg)
    fg.add_to(m)

add_raster_fg(dsm_png,       dsm_4326,       "DSM")
add_raster_fg(dtm_png,       dtm_4326,       "DTM")
add_raster_fg(height_png,    dsm_4326,       "Height")
add_raster_fg(year_png,      year_4326,      "Year")
add_raster_fg(roofs_png,     roofs_4326,     "Roofs (RGB)")
add_raster_fg(drone_low_png, drone_low_4326, "Drone Low RGB")
add_raster_fg(drone_hr_png,  drone_hr_4326,  "Drone High RGB")

# ─────────────────────────────────────────
# VECTOR LAYERS
# ─────────────────────────────────────────
gdf = santo_domingo.to_crs(4326)

def hex_color_from_cmap(val, vmin, vmax, cmap):
    n = np.clip((val - vmin) / (vmax - vmin + 1e-9), 0, 1)
    r, g, b, _ = cmap(n)
    return "#{:02x}{:02x}{:02x}".format(int(r*255), int(g*255), int(b*255))

# Roof classes → 4 colors
roof_classes = sorted(gdf["roof"].dropna().unique())[:4]
roof_color_map = {cls: ROOF_COLORS[i % 4] for i, cls in enumerate(roof_classes)}

def make_vector_fg(name, style_fn, show=False, tooltip_fields=None):
    fg = folium.FeatureGroup(name=name, overlay=True, show=show)
    tt_fields = tooltip_fields or ["id", "height", "roof", "year", "survey_height", "height_error"]
    tt_fields = [f for f in tt_fields if f in gdf.columns]
    folium.GeoJson(
        gdf,
        style_function=style_fn,
        tooltip=folium.GeoJsonTooltip(fields=tt_fields, sticky=True),
    ).add_to(fg)
    fg.add_to(m)

# Default white outlines
def style_default(feat):
    return {"fillColor": "white", "color": "black", "weight": 2, "fillOpacity": 0.3, "opacity": 1}

# Elevation-tinted (for DTM / DSM / Height)
def make_style_elev(col, vmin, vmax):
    def fn(feat):
        v = feat["properties"].get(col)
        c = hex_color_from_cmap(float(v), vmin, vmax, CMAP_ELEV) if v is not None else "#888888"
        return {"fillColor": c, "color": "black", "weight": 1, "fillOpacity": 0.6, "opacity": 0.8}
    return fn

# Year-tinted
def style_year(feat):
    v = feat["properties"].get("year")
    c = hex_color_from_cmap(float(v), vmin_yr, vmax_yr, CMAP_YEAR) if v is not None else "#888888"
    return {"fillColor": c, "color": "black", "weight": 1, "fillOpacity": 0.6, "opacity": 0.8}

# Roof categorical
def style_roof(feat):
    cls = feat["properties"].get("roof")
    c   = roof_color_map.get(cls, "#aaaaaa")
    return {"fillColor": c, "color": "black", "weight": 1, "fillOpacity": 0.6, "opacity": 0.8}

# height_error_abs — green→red
def style_err(feat):
    v = feat["properties"].get("height_error_abs") or feat["properties"].get("height_error")
    if v is None:
        return {"fillColor": "#888888", "color": "black", "weight": 1, "fillOpacity": 0.6}
    c = hex_color_from_cmap(float(v), vmin_err, vmax_err, CMAP_ERR)
    return {"fillColor": c, "color": "black", "weight": 1, "fillOpacity": 0.6, "opacity": 0.8}

make_vector_fg("Buildings – default",   style_default,              show=True)
make_vector_fg("Buildings – DSM/DTM",   make_style_elev(_sh_col, vmin_sh, vmax_sh), show=False)
make_vector_fg("Buildings – Height",    make_style_elev("height", vmin_h, vmax_h),       show=False)
make_vector_fg("Buildings – Year",      style_year,                 show=False)
make_vector_fg("Buildings – Roof type", style_roof,                 show=False)
make_vector_fg("Buildings – Height error", style_err,               show=False)

# ─────────────────────────────────────────
# LAYER CONTROL
# ─────────────────────────────────────────
folium.LayerControl(collapsed=False, position="topright").add_to(m)

# ─────────────────────────────────────────
# RASTER DROPDOWN + SYNC LOGIC  (JS)
# ─────────────────────────────────────────
raster_layers = ["DSM", "DTM", "Height", "Year", "Roofs (RGB)", "Drone Low RGB", "Drone High RGB"]
raster_layers_js = json.dumps(raster_layers)

# Map: raster name → vector companion name
raster_to_vector = {
    "DSM":         "Buildings – DSM/DTM",
    "DTM":         "Buildings – DSM/DTM",
    "Height":      "Buildings – Height",
    "Year":        "Buildings – Year",
    "Roofs (RGB)": "Buildings – Roof type",
}
raster_to_vector_js = json.dumps(raster_to_vector)

dropdown_html = f"""
<div id="raster-ctrl" style="
    position:fixed; top:10px; left:10px; z-index:9999;
    background:white; padding:10px 14px; border:1px solid #ccc;
    border-radius:8px; font-family:sans-serif; font-size:13px;
    box-shadow:0 2px 8px rgba(0,0,0,.18);">
  <b style="font-size:14px;">Thematic raster</b><br>
  <select id="rasterSelect" style="margin-top:6px;width:170px;font-size:13px;">
    <option value="None">— none —</option>
    {''.join(f'<option value="{x}">{x}</option>' for x in raster_layers)}
  </select>
</div>

<script>
(function(){{
  var RASTER_LAYERS = {raster_layers_js};
  var RASTER_TO_VEC = {raster_to_vector_js};

  function getLayerCheckboxes() {{
    var map = {{}};
    document.querySelectorAll('.leaflet-control-layers-overlays label').forEach(function(lbl) {{
      var txt = lbl.innerText.trim();
      var inp = lbl.querySelector('input');
      if(inp) map[txt] = inp;
    }});
    return map;
  }}

  function setLayer(name, on) {{
    var cbs = getLayerCheckboxes();
    if(cbs[name] && cbs[name].checked !== on) cbs[name].click();
  }}

  document.getElementById('rasterSelect').addEventListener('change', function(e) {{
    var sel = e.target.value;

    // Turn off all raster layers first
    RASTER_LAYERS.forEach(function(r) {{ setLayer(r, false); }});

    // Turn off all vector companions except default and error
    Object.values(RASTER_TO_VEC).forEach(function(v) {{ setLayer(v, false); }});

    if(sel !== 'None') {{
      setLayer(sel, true);
      var vec = RASTER_TO_VEC[sel];
      if(vec) {{
        setLayer('Buildings – default', false);
        setLayer(vec, true);
      }}
    }} else {{
      setLayer('Buildings – default', true);
    }}
  }});
}})();
</script>
"""

m.get_root().html.add_child(folium.Element(dropdown_html))

# ─────────────────────────────────────────
# LEGENDS
# ─────────────────────────────────────────
# All legend "cards" live inside a single fixed container (#legend-stack) and
# are individually shown/hidden by the generic layer-watcher script below.
# This avoids the old per-legend `position:fixed` overlap problem and the
# broken gradient-stop bug (the previous version mapped colors to the wrong
# percentages, so almost the entire bar rendered as the vmax color).

def gradient_legend(lid, title, cmap, vmin, vmax, n=11):
    """Build an evenly-spaced linear-gradient legend (n stops from vmin to vmax)."""
    stops = []
    for i in range(n):
        r, g, b, _ = cmap(i / (n - 1))
        hexcol = "#{:02x}{:02x}{:02x}".format(int(r*255), int(g*255), int(b*255))
        pct = 100 * i / (n - 1)
        stops.append(f"{hexcol} {pct:.1f}%")
    gradient = ",".join(stops)
    return f"""
<div id="legend-{lid}" class="map-legend" style="
    display:none; background:white; padding:10px 14px; border:1px solid #bbb; border-radius:8px;
    font-family:sans-serif; font-size:12px; box-shadow:0 2px 8px rgba(0,0,0,.15);">
  <b>{title}</b>
  <div style="margin-top:6px;width:200px;height:16px;
      background:linear-gradient(to right,{gradient});border:1px solid #aaa;"></div>
  <div style="display:flex;justify-content:space-between;width:200px;margin-top:3px;">
    <span>{vmin:.1f}</span><span>{vmax:.1f}</span>
  </div>
</div>"""

def categorical_legend(lid, title, classes, colors):
    items = "".join(f"""
    <div style="display:flex;align-items:center;margin-top:4px;">
      <div style="width:14px;height:14px;background:{c};border:1px solid #555;margin-right:6px;"></div>
      <span>{cls}</span>
    </div>""" for cls, c in zip(classes, colors))
    return f"""
<div id="legend-{lid}" class="map-legend" style="
    display:none; background:white; padding:10px 14px; border:1px solid #bbb; border-radius:8px;
    font-family:sans-serif; font-size:12px; box-shadow:0 2px 8px rgba(0,0,0,.15);">
  <b>{title}</b>{items}
</div>"""

legends_html = (
    gradient_legend("DSM",    "DSM (m)",       CMAP_ELEV, legend_vmin_elev, legend_vmax_elev) +
    gradient_legend("DTM",    "DTM (m)",       CMAP_ELEV, legend_vmin_elev, legend_vmax_elev) +
    gradient_legend("Buildings___DSM_DTM", "Street height (m)", CMAP_ELEV, legend_vmin_sh, legend_vmax_sh) +
    gradient_legend("Height", "Height (m)",    CMAP_ELEV, legend_vmin_h,    legend_vmax_h   ) +
    gradient_legend("Year",   "Year",          CMAP_YEAR, legend_vmin_yr,   legend_vmax_yr  ) +
    categorical_legend("Roofs__RGB_", "Roof type", roof_classes, [roof_color_map[c] for c in roof_classes]) +
    gradient_legend("Buildings___Height_error",
                    "Height error (m)", CMAP_ERR,
                    legend_vmin_err, legend_vmax_err)
)

legend_stack_html = f"""
<div id="legend-stack" style="
    position:fixed; bottom:30px; left:10px; z-index:9999;
    display:flex; flex-direction:column; gap:8px;">
  {legends_html}
</div>
"""

m.get_root().html.add_child(folium.Element(legend_stack_html))

# ─────────────────────────────────────────
# GENERIC LEGEND <-> LAYER-CONTROL SYNC
# ─────────────────────────────────────────
# Maps the (exact) name shown in the Folium LayerControl to the legend(s)
# that should be visible while that layer is checked. A legend can be shared
# by multiple layers (e.g. raster "Height" and "Buildings – Height" both use
# the Height legend, so it stays visible if either is on).
LAYER_LEGEND_MAP = {
    "DSM":                      ["DSM"],
    "DTM":                      ["DTM"],
    "Height":                   ["Height"],
    "Year":                     ["Year"],
    "Roofs (RGB)":              ["Roofs__RGB_"],
    "Buildings – DSM/DTM":      ["Buildings___DSM_DTM"],
    "Buildings – Height":       ["Height"],
    "Buildings – Year":         ["Year"],
    "Buildings – Roof type":    ["Roofs__RGB_"],
    "Buildings – Height error": ["Buildings___Height_error"],
}
layer_legend_map_js = json.dumps(LAYER_LEGEND_MAP)

legend_sync_js = f"""
<script>
(function(){{
  var LAYER_LEGEND_MAP = {layer_legend_map_js};

  function getLayerCheckboxes() {{
    var map = {{}};
    document.querySelectorAll('.leaflet-control-layers-overlays label').forEach(function(lbl) {{
      var txt = lbl.innerText.trim();
      var inp = lbl.querySelector('input');
      if(inp) map[txt] = inp;
    }});
    return map;
  }}

  function syncLegends() {{
    var cbs = getLayerCheckboxes();
    var needed = {{}};

    Object.keys(LAYER_LEGEND_MAP).forEach(function(layerName) {{
      var inp = cbs[layerName];
      if(inp && inp.checked) {{
        LAYER_LEGEND_MAP[layerName].forEach(function(legendId) {{ needed[legendId] = true; }});
      }}
    }});

    document.querySelectorAll('#legend-stack .map-legend').forEach(function(div) {{
      var id = div.id.replace(/^legend-/, '');
      div.style.display = needed[id] ? 'block' : 'none';
    }});
  }}

  function init() {{
    var cbs = getLayerCheckboxes();
    if(Object.keys(cbs).length === 0) {{ setTimeout(init, 300); return; }}

    // Re-check on every click of any overlay checkbox
    document.querySelectorAll('.leaflet-control-layers-overlays input').forEach(function(inp) {{
      inp.addEventListener('change', syncLegends);
    }});

    syncLegends();
  }}

  setTimeout(init, 800);
}})();
</script>
"""
m.get_root().html.add_child(folium.Element(legend_sync_js))

# ─────────────────────────────────────────
# CLICK POPUP FOR NUMERIC RASTERS
# ─────────────────────────────────────────
# Embed raster data + bounds so JS can interpolate click → pixel value
raster_data_js = f"""
<script>
var RASTER_DATA = {{
  "DSM":    {{ data: {dsm_js},    bounds: {list(dsm_4326)},    vmin: {vmin_elev:.2f}, vmax: {vmax_elev:.2f} }},
  "DTM":    {{ data: {dtm_js},    bounds: {list(dtm_4326)},    vmin: {vmin_elev:.2f}, vmax: {vmax_elev:.2f} }},
  "Height": {{ data: {height_js}, bounds: {list(dsm_4326)},    vmin: {vmin_h:.2f},    vmax: {vmax_h:.2f}    }},
  "Year":   {{ data: {year_js},   bounds: {list(year_4326)},   vmin: {vmin_yr},       vmax: {vmax_yr}       }}
}};

var activeRaster = null;
document.getElementById('rasterSelect').addEventListener('change', function(e) {{
  activeRaster = e.target.value === 'None' ? null : e.target.value;
}});

function getRasterValue(layerName, lat, lng) {{
  var d = RASTER_DATA[layerName];
  if(!d || !d.data) return null;
  var bounds = d.bounds; // [left, bottom, right, top]
  var rows = d.data.length, cols = d.data[0].length;
  var col = Math.round((lng - bounds[0]) / (bounds[2] - bounds[0]) * (cols - 1));
  var row = Math.round((bounds[3] - lat) / (bounds[3] - bounds[1]) * (rows - 1));
  if(row < 0 || row >= rows || col < 0 || col >= cols) return null;
  return d.data[row][col];
}}

// Attach click handler after map is ready
setTimeout(function() {{
  var mapEl = document.querySelector('.folium-map') || document.getElementById('map');
  if(!mapEl) return;
  // Access the Leaflet map instance
  var mapKeys = Object.keys(window).filter(function(k) {{ return k.startsWith('map_'); }});
  if(mapKeys.length === 0) return;
  var leafletMap = window[mapKeys[0]];

  leafletMap.on('click', function(e) {{
    if(!activeRaster || !RASTER_DATA[activeRaster]) return;
    var val = getRasterValue(activeRaster, e.latlng.lat, e.latlng.lng);
    if(val === null || val === undefined) return;
    var label = activeRaster === 'Year' ? Math.round(val).toString() : val.toFixed(2) + ' m';
    L.popup()
      .setLatLng(e.latlng)
      .setContent('<b>' + activeRaster + '</b>: ' + label)
      .openOn(leafletMap);
  }});
}}, 1500);
</script>
"""

m.get_root().html.add_child(folium.Element(raster_data_js))

# ─────────────────────────────────────────
# UNLOCK ZOOM BEYOND MAX NATIVE ZOOM
# ─────────────────────────────────────────
# Sets maxZoom=22 on the Leaflet map object directly after init,
# and also removes the zoom cap Leaflet enforces via setMaxZoom.
# This lets the user pinch/scroll zoom deeper into ImageOverlay tiles
# without requesting tiles at unsupported zoom levels.
zoom_unlock_js = """
<script>
setTimeout(function() {
  var mapKeys = Object.keys(window).filter(function(k){ return k.startsWith('map_'); });
  if(!mapKeys.length) return;
  var lmap = window[mapKeys[0]];
  lmap.setMaxZoom(22);
  // For each ImageOverlay layer, allow rendering at higher zoom
  lmap.eachLayer(function(layer) {
    if(layer instanceof L.ImageOverlay) {
      layer.options.maxZoom = 22;
    }
  });
}, 800);
</script>
"""
m.get_root().html.add_child(folium.Element(zoom_unlock_js))

# ─────────────────────────────────────────
# SAVE
# ─────────────────────────────────────────
m.save("/home/miguel/Documents/UNI/Master/2/TFM/presentation/maps/remote_sensing.html")
print("Saved remote_sensing.html")