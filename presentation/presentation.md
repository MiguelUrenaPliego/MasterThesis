---
marp: true
theme: default_theme
paginate: true
html: true
header: " "
footer: " "
math: katex
---

<!-- _class: title two-line-logos -->
<h1></h1>
<h2></h2>


---

<!--header: "Background"-->


# Seismic risk

<div style="display: flex; justify-content: center; align-items: center; height: 80vh;">

<div style="transform: scale(1.3); transform-origin: center;">

$$
\text{Risk} =
\text{Hazard} \;\cdot\;
\text{Exposure} \;\cdot\;
\text{Vulnerability}
$$

</div>

</div>

---

<!-- header: "Background" -->
<!-- _class: col2-50 -->

# ADELANTE 2

<div class="col-row">

<div class="col-left">


- International Cooperation Project

- 3 pilot neighbourhoods  
  - Guatemala City District 1  
  - San José (Costa Rica)  
  - Santo Domingo (Dominican Republic)

- Field surveys: structural material + other parameters

- Remote surveys (QGIS)

- Manual footprint segmentation

</div>

<div class="col-right">

<div class="img-frame">

<a href="https://www.mideplan.go.cr/proyecto-de-cooperacion-triangular-busca-contribuir-reducir-el-riesgo-sismico-en-latinoamerica">
<img src="figures/adelante2.jpg" alt="ADELANTE 2 project">
</a>

</div>

</div>

</div>

---

<!--header: "Background"-->

# Seismic risk

<div style="display: flex; justify-content: center; align-items: center; height: 80vh;">

<div style="transform: scale(1.5); transform-origin: center;">

$$
\text{Risk} =
\text{Hazard} \;\cdot\;
\fbox{\text{Exposure}} \;\cdot\;
\fbox{\text{Vulnerability}}
$$

</div>

</div>

---

<!--header: "Background"-->

#  

<div style="display: flex; justify-content: center; align-items: center; height: 80vh;">

<div style="transform: scale(1.5); transform-origin: center;">

$$
\text{Risk} =
\text{Hazard} \;\cdot\;
\fbox{\text{Exposure}} \;\cdot\;
\text{Vulnerability}
$$

</div>

</div>

---


<!--header: "Introduction"-->

# The building's DNA

<div class="img-frame">

<div style="background:white; padding:150px; display:inline-block;">

![DNA structure of the building](figures/DNA.jpg)

</div>
</div>

---

<!-- header: "Introduction" -->
<!-- _class: col2-55 img-align img-align-0 -->

<div class="onecolumn">

# Two different worlds...

</div>

<div class="col-row">
<div class="col-left">

![Structural engineering](figures/buildings_simulation.jpg)

<span class="caption">Structural engineering</span>

</div>
<div class="col-right">

![Remote sensing](figures/roof_mat.jpg)

<span class="caption">Remote sensing</span>

</div>
</div>

---

<!-- header: "Methodology" -->
<!-- _class: col2-50 -->

# Step 1. Footprint segmentation


<div class="col-row">

<div class="col-left">

- Mask2Former: instance segmentation fine-tuned model  

- SAM2: assisted segmentation 

- Microsoft GlobalMLBuildingFootprints dataset  

</div>

<div class="col-right">

<div class="img-frame">

![SAM2 example](figures/sam2_test.jpg)

<span class="caption">SAM2 example</span>

</div>

</div>

</div>

---

<!--header: ""-->
<!-- _class: col2-50 -->

<div class="col-row">

<div class="col-left" style="justify-content:flex-start; align-items:flex-start;">

# Step 1. Results

<div style="display:flex; gap:30px; align-items:flex-start; width:100%;">

<div style="flex:1; font-size:20px; line-height:1.3; margin-top:80px">

<table style="border-collapse:collapse; width:100%;">

<thead>
<tr>
<th style="border:1px solid #999; padding:10px 18px;">Metric</th>
<th style="border:1px solid #999; padding:10px 28px;">Mask2Former</th>
<th style="border:1px solid #999; padding:10px 28px;">SAM2</th>
<th style="border:1px solid #999; padding:10px 28px;">Microsoft</th>
</tr>
</thead>

<tbody>

<tr>
<td style="border:1px solid #999; padding:10px 18px;">AJ</td>
<td style="border:1px solid #999; padding:10px 28px;">0.580</td>
<td style="border:1px solid #999; padding:10px 28px;">0.630</td>
<td style="border:1px solid #999; padding:10px 28px;">0.099</td>
</tr>

<tr>
<td style="border:1px solid #999; padding:10px 18px;">SBD</td>
<td style="border:1px solid #999; padding:10px 28px;">0.560</td>
<td style="border:1px solid #999; padding:10px 28px;">0.737</td>
<td style="border:1px solid #999; padding:10px 28px;">0.124</td>
</tr>

<tr>
<td style="border:1px solid #999; padding:10px 18px;">PQ</td>
<td style="border:1px solid #999; padding:10px 28px;">0.446</td>
<td style="border:1px solid #999; padding:10px 28px;">0.530</td>
<td style="border:1px solid #999; padding:10px 28px;">0.002</td>
</tr>

<tr>
<td style="border:1px solid #999; padding:10px 18px;">mAP</td>
<td style="border:1px solid #999; padding:10px 28px;">0.224</td>
<td style="border:1px solid #999; padding:10px 28px;">0.277</td>
<td style="border:1px solid #999; padding:10px 28px;">0.0003</td>
</tr>

<tr>
<td style="border:1px solid #999; padding:10px 18px;">sAP</td>
<td style="border:1px solid #999; padding:10px 28px;">0.370</td>
<td style="border:1px solid #999; padding:10px 28px;">0.526</td>
<td style="border:1px solid #999; padding:10px 28px;">0.044</td>
</tr>

</tbody>

</table>

</div>

</div>

</div>

<div class="col-right">

<div class="img-caption">

<div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; font-size:20px; text-align:center">

  <div>
    <div style="width:100%; aspect-ratio:1/1;">
      <img src="figures/guat_30cm_gt.jpg"
           style="width:100%; height:100%; object-fit:cover;">
    </div>
    <div>Guatemala GT</div>
  </div>

  <div>
    <div style="width:100%; aspect-ratio:1/1;">
      <img src="figures/mask2former_guat_30cm.jpg"
           style="width:100%; height:100%; object-fit:cover;">
    </div>
    <div>Mask2Former</div>
  </div>

  <div>
    <div style="width:100%; aspect-ratio:1/1;">
      <img src="figures/SAM2_guat.jpg"
           style="width:100%; height:100%; object-fit:cover;">
    </div>
    <div>SAM2</div>
  </div>

  <div>
    <div style="width:100%; aspect-ratio:1/1;">
      <img src="figures/guatemala_microsoft.jpg"
           style="width:100%; height:100%; object-fit:cover;">
    </div>
    <div>Microsoft</div>
  </div>

</div>

</div>

</div>

--- 

<!--header: "Use case"-->

# [Transport surface segmentation](https://www.sciencedirect.com/science/article/pii/S2352938525000564?via%3Dihub)

<div style="height:90%; aspect-ratio:16/9; margin:auto;">
  <a href="https://www.sciencedirect.com/science/article/pii/S2352938525000564?via%3Dihub">
    <img
      src="figures/elsevier_paper.jpg"
      style="width:100%; height:100%; object-fit:contain; display:block;"
    >
  </a>
</div>

---

<!-- _class: no-header no-margin no-footer -->

<div class="body">
<iframe
  src="maps/madrid_transport_map.html"
  style="width: 100%; height: 100%; border: w; margin-top: 0rem">
</iframe>
</div>

---

<!-- header: "Methodology" -->
<!-- _class: col2-50 img-align img-align-70 -->

<div class="onecolumn">

# Step 2. Relative position

</div>

<div class="col-row">

<div class="col-left">

<div class="img-bg-white" style="--img-pad: 20px;">

![Relative position concept](figures/relative_position_explanation.jpg)

</div>

<span class="caption">Relative position concept</span>

</div>

<div class="col-right">

<div class="img-bg-white" style="--img-pad: 0px;">

![Relative position results](figures/relative_position_confusion_matrix.jpg)

</div>

<span class="caption">Relative position results</span>

</div>

</div>

---

<!-- _class: no-header no-margin no-footer -->


<div class="body">
<iframe
  src="maps/pilot_regions_map.html"
  style="width: 100%; height: 100%; border: w; margin-top: 0rem">
</iframe>
</div>

---

<!-- header: "Methodology" -->
<!-- _class: col2-50 img-align img-align-80 -->

<div class="onecolumn">

# Step 3. Shape: Basic footprint sizes

</div>

<div class="col-row">

<div class="col-left">

<div class="img-bg-white" style="--img-pad: 20px;">

![Eccentricity](figures/box_idealization_and_eccentricity.jpg)

</div>

<span class="caption">Eccentricity</span>

</div>

<div class="col-right">

<div class="img-bg-white" style="--img-pad: 20px;">

![GNDT basic sizes](figures/basic_lengths_example.jpg)

</div>

<span class="caption">GNDT basic sizes</span>

</div>

</div>

---

<!-- header: "Use case" -->
<!-- _class: col2-50 img-align img-align-73 -->

<div class="onecolumn">

# Step 3. Shape: Results

</div>

<div class="col-row">
<div class="col-left">

![Eccentricity](figures/eccentricity_san_jose.jpg)

<span class="caption">Eccentricity</span>

</div>

<div class="col-right">

![Slenderness in San José (Costa Rica)](figures/slenderness_san_jose.jpg)

<span class="caption">Slenderness in San José (Costa Rica)</span>

</div>
</div>

---

<!--
header: "Use case"
-->

# [Footprint attributes](https://link.springer.com/article/10.1186/s40323-026-00323-y)

<div style="height:90%; aspect-ratio:16/9; margin:auto;">
  <a href="https://link.springer.com/article/10.1186/s40323-026-00323-y">
    <img
      src="figures/springer_paper.jpg"
      style="width:100%; height:100%; object-fit:contain; display:block;"
    >
  </a>
</div>

---

<!-- _class: no-header no-margin no-footer -->


<div class="body">
<iframe
  src="maps/pilot_regions_map.html"
  style="width: 100%; height: 100%; border: w; margin-top: 0rem">
</iframe>
</div>

---

<!--
header: "Methodology"
-->

# Step 4. Height

<div style="display:flex; gap:40px; align-items:center; margin-top:10px;">

<div style="flex:1; text-align:left;">

- Aerial imagery: drone, plane or high-resolution satellite imagery  

- Photogrammetry → Digital Surface Model (DSM)  
- Street elevations → Digital Terrain Model (DTM)  
- <b>Height = DSM − DTM</b>

</div>

<div style="flex:1; display:flex; flex-direction:column; align-items:center;">

  <div style="
      width:100%;
      aspect-ratio:4/3;
      overflow:hidden;
      display:flex;
  ">
    <img src="figures/height.jpg"
         style="
           width:100%;
           height:100%;
           object-fit:cover;
           display:block;
         ">
  </div>

  <div style="margin-top:10px; line-height:1; font-size:30px ">
  <em>DSM – Santo Domingo (DR)</em>

  </div>

</div>

</div>

---

<!-- header: "Methodology" -->
<!-- _class: col2-50 img-align img-align-70 -->

<div class="onecolumn">

# Step 5. Remote sensing

</div>

<div class="col-row">
<div class="col-left">

![Year of first construction](figures/year.jpg)

<span class="caption">Year of first construction</span>

</div>

<div class="col-right">

![Unsupervised multispectral classification](figures/roof_mat.jpg)

<span class="caption">Unsupervised multispectral classification</span>

</div>
</div>

---

<!-- _class: no-header no-margin no-footer -->


<div class="body">
<iframe
  src="maps/remote_sensing.html"
  style="width: 100%; height: 100%; border: w; margin-top: 0rem">
</iframe>
</div>

---

<!-- header: "Methodology" -->
<!-- _class: col2-45 img-align img-align-60 -->

<div class="onecolumn">

# Step 6. Structural system classifier

</div>

<div class="col-row">
<div class="col-left">

![Structural system prediction](figures/structural_system_Guatemala.jpg)

<span class="caption">Structural system prediction</span>

</div>

<div class="col-right">

![SHAP values for Logistic Regression](figures/LR_weights.jpg)

<span class="caption">SHAP values for Logistic Regression</span>

</div>
</div>

---

<!-- _class: no-header no-margin no-footer -->


<div class="body">
<iframe
  src="maps/ml_results_map.html"
  style="width: 100%; height: 100%; border: w; margin-top: 0rem">
</iframe>
</div>

---

<!--header: ""-->


<div style="display: flex; justify-content: center; align-items: center; height: 80vh;">

<div style="transform: scale(1.5); transform-origin: center;">

$$
\text{Risk} =
\text{Hazard} \;\cdot\;
\text{Exposure} \;\cdot\;
\fbox{\text{Vulnerability}}
$$

</div>

</div>

---

<!-- header: "Methodology" -->
<!-- _class: col2-50 img-align -->

<div class="onecolumn">

# Step 7. Capacity curve generation

</div>

<div class="col-row">

<div class="col-left">

- Idealized building configurations 

- Auto generation of FEM models  

- Capacity curve training set 

- Functional regression model 

- Inference with real building params  

</div>

<div class="col-right">

![Finite Element Model in OpenSees](figures/buildings_simulation.jpg)

<span class="caption">Finite Element Model in OpenSees</span>

</div>

</div>


--- 

<!-- header: "Methodology" -->
<!-- _class: img-align img-align-0 -->

# Step 7. Capacity curve generation

<div style="height:75vh; display:flex; flex-direction:column; justify-content:center; align-items:center; text-align:center;">

<table style="border-collapse:collapse; font-size:20px; text-align:center">

<thead>
<tr>
<th style="border:1px solid #999; padding:10px 18px;">Metric</th>
<th style="border:1px solid #999; padding:10px 28px;">Without Bias Correction</th>
<th style="border:1px solid #999; padding:10px 28px;">With Conservative Bias</th>
</tr>
</thead>

<tbody>

<tr>
<td style="border:1px solid #999; padding:10px 18px;">R2 Score</td>
<td style="border:1px solid #999; padding:10px 28px;">0.795</td>
<td style="border:1px solid #999; padding:10px 28px;">0.776</td>
</tr>

<tr>
<td style="border:1px solid #999; padding:10px 18px;">RMSE</td>
<td style="border:1px solid #999; padding:10px 28px;">0.161</td>
<td style="border:1px solid #999; padding:10px 28px;">0.168</td>
</tr>

<tr>
<td style="border:1px solid #999; padding:10px 18px;">MAE</td>
<td style="border:1px solid #999; padding:10px 28px;">0.097</td>
<td style="border:1px solid #999; padding:10px 28px;">0.107</td>
</tr>

<tr>
<td style="border:1px solid #999; padding:10px 18px;">% Below</td>
<td style="border:1px solid #999; padding:10px 28px;">51.0%</td>
<td style="border:1px solid #999; padding:10px 28px;">72.1%</td>
</tr>

</tbody>

</table>

<p style="margin-top:25px;">Gaussian process regression results</p>

</div>

---

<!--
header: "Methodology"
-->

# Step 6. Capacity curve generation

<div style="height:90%; aspect-ratio:16/9;">
  <img
    src="figures/example_curve.jpg"
    style="width:100%; height:100%;"
  >
</div>

---

<!--
header: "Use case"
-->

# Step 6. Capacity curve generation

<div style="
  background: white;
  padding: 12px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.08);
  width: 100%;
  position: relative;
">

  <!-- Zoom buttons -->
  <div style="position:absolute; top:20px; left:20px; z-index:10;">
    <button id="zoom-in" style="font-size:18px; padding:6px 10px;">+</button>
    <button id="zoom-out" style="font-size:18px; padding:6px 10px;">−</button>
  </div>

  <div id="viewer" style="width:100%; height:470px;"></div>

</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/openseadragon/4.1.1/openseadragon.min.js"></script>

<script>
const viewer = OpenSeadragon({
  id: "viewer",
  tileSources: {
    type: "image",
    url: "figures/all_curves.jpg"
  },
  showNavigator: true,
  defaultZoomLevel: 0,
  minZoomLevel: 0.5,
  maxZoomLevel: 10,
  gestureSettingsMouse: {
    clickToZoom: true,
    dblClickToZoom: true
  }
});

// + button
document.getElementById("zoom-in").addEventListener("click", function () {
  viewer.viewport.zoomBy(1.2);
  viewer.viewport.applyConstraints();
});

// − button
document.getElementById("zoom-out").addEventListener("click", function () {
  viewer.viewport.zoomBy(0.8);
  viewer.viewport.applyConstraints();
});
</script>

---

<!--
header: "Methodology"
-->

# Step 6. Next steps

<div style="height:90%; aspect-ratio:16/9;">
  <img
    src="figures/autoencoder.jpg"
    style="width:100%; height:100%;"
  >
</div>

---

<!--
header: "Methodology"
-->

# Step 7. Evacuation 

Accessibility values (0-red 1-green) as a function of height and walking distance

<div style="flex:1; font-size:22px; line-height:1.2; margin-top:20px; text-align:center">

<table style="border-collapse:collapse; width:100%; table-layout:fixed;">

<thead>
<tr>
<th style="border:1px solid #999; padding:6px;">
  Walking (m) → Height (m) ↓
</th>

<th style="border:1px solid #999; padding:6px;">50</th>
<th style="border:1px solid #999; padding:6px;">100</th>
<th style="border:1px solid #999; padding:6px;">150</th>
<th style="border:1px solid #999; padding:6px;">200</th>
<th style="border:1px solid #999; padding:6px;">250</th>
<th style="border:1px solid #999; padding:6px;">300</th>
<th style="border:1px solid #999; padding:6px;">350</th>
<th style="border:1px solid #999; padding:6px;">400</th>
<th style="border:1px solid #999; padding:6px;">450</th>
</tr>
</thead>

<tbody>

<!-- 0.0 -->
<tr>
<td style="border:1px solid #999; padding:6px;">0.0</td>
<td style="background:#ff4d4d;">0</td>
<td style="background:#ff4d4d;">0</td>
<td style="background:#ff4d4d;">0</td>
<td style="background:#ff4d4d;">0</td>
<td style="background:#ff4d4d;">0</td>
<td style="background:#ff4d4d;">0</td>
<td style="background:#ff4d4d;">0</td>
<td style="background:#ff4d4d;">0</td>
<td style="background:#ff4d4d;">0</td>
</tr>

<!-- 0.2 -->
<tr>
<td style="border:1px solid #999; padding:6px;">0.2</td>
<td style="background:#ffb84d;">0.2</td>
<td style="background:#ffb84d;">0.2</td>
<td style="background:#ffb84d;">0.2</td>
<td style="background:#ffb84d;">0.2</td>
<td style="background:#ffb84d;">0.2</td>
<td style="background:#ffb84d;">0.2</td>
<td style="background:#ffb84d;">0.2</td>
<td style="background:#ffb84d;">0.2</td>
<td style="background:#ff4d4d;">0</td>
</tr>

<!-- 0.4 -->
<tr>
<td style="border:1px solid #999; padding:6px;">0.4</td>
<td style="background:#ffcc66;">0.4</td>
<td style="background:#ffcc66;">0.4</td>
<td style="background:#ffb84d;">0.2</td>
<td style="background:#ffb84d;">0.2</td>
<td style="background:#ffb84d;">0.2</td>
<td style="background:#ffb84d;">0.2</td>
<td style="background:#ffb84d;">0.2</td>
<td style="background:#ffb84d;">0.2</td>
<td style="background:#ff4d4d;">0</td>
</tr>

<!-- 0.6 -->
<tr>
<td style="border:1px solid #999; padding:6px;">0.6</td>
<td style="background:#a6e36d;">0.6</td>
<td style="background:#a6e36d;">0.6</td>
<td style="background:#ffcc66;">0.4</td>
<td style="background:#ffcc66;">0.4</td>
<td style="background:#ffcc66;">0.4</td>
<td style="background:#ffb84d;">0.2</td>
<td style="background:#ffb84d;">0.2</td>
<td style="background:#ffb84d;">0.2</td>
<td style="background:#ff4d4d;">0</td>
</tr>

<!-- 0.8 -->
<tr>
<td style="border:1px solid #999; padding:6px;">0.8</td>
<td style="background:#7ed957;">0.8</td>
<td style="background:#a6e36d;">0.6</td>
<td style="background:#a6e36d;">0.6</td>
<td style="background:#ffcc66;">0.4</td>
<td style="background:#ffcc66;">0.4</td>
<td style="background:#ffb84d;">0.2</td>
<td style="background:#ffb84d;">0.2</td>
<td style="background:#ffb84d;">0.2</td>
<td style="background:#ff4d4d;">0</td>
</tr>

<!-- 1.0 -->
<tr>
<td style="border:1px solid #999; padding:6px;">1.0</td>
<td style="background:#2ecc71;">1.0</td>
<td style="background:#7ed957;">0.8</td>
<td style="background:#7ed957;">0.8</td>
<td style="background:#a6e36d;">0.6</td>
<td style="background:#a6e36d;">0.6</td>
<td style="background:#ffcc66;">0.4</td>
<td style="background:#ffcc66;">0.4</td>
<td style="background:#ffb84d;">0.2</td>
<td style="background:#ff4d4d;">0</td>
</tr>

</tbody>

</table>

</div>

---

<!-- _class: no-header no-margin no-footer -->

<div class="body">
<iframe
  src="maps/tsunami_access_map.html"
  style="width: 100%; height: 100%; border: w; margin-top: 0rem">
</iframe>
</div>

---


<!-- _class: no-header no-margin no-footer -->

<div class="body">
<iframe
  src="maps/tsunami_population_map.html"
  style="width: 100%; height: 100%; border: w; margin-top: 0rem">
</iframe>
</div>

---

<!--
header: ""
-->

# Conclusions

- Based on international and local building codes

- Building-level data with minimum or no field surveys or cadastral data

- Automated **10 out of 13** GEM attributes

- All relevant data to create fragility curves

- Fast and building specific capacity curve inference

- All relevant data to create fragility curves

- Impact and evacuation

---

# Main scientific collaborations 

- Advanced Geomatics Group (AGA), ETSI Caminos, Canales y Puertos, UPM, Madrid, Spain

- Department of Forestry and Environmental Engineering and Management, UPM, Madrid, Spain
- Institute of Transportation, TU Wien, Austria
- PIMM Laboratory, ENSAM Institute of Technology, Paris, France
- City Science Group, MIT Media Lab, Massachusetts Institute of Technology, Cambridge, USA
- Instituto Tecnológico de Santo Domingo (INTEC), Santo Domingo, Dominican Republic
- Universidad de Costa Rica (UCR), San José, Costa Rica
- Universidad de San Carlos de Guatemala (USAC), Ciudad de Guatemala, Guatemala

---

# Code and papers

- Seismic risk workflow: [SeismicBuildingExposure](https://github.com/GeomaticsCaminosUPM/SeismicBuildingExposure)

- Image vision datasets and models: [GeoImageDataset](https://github.com/GeomaticsCaminosUPM/GeoVisionDataset)

- Accessibility and evacuation: [UrbanAccessAnalyzer](https://github.com/CityScope/UrbanAccessAnalyzer)

- Paper image vision and street view height estimation: [MDPI](https://www.mdpi.com/2076-3417/13/8/5037)

- Paper transport surface estimation: [Elsevier](https://www.sciencedirect.com/science/article/pii/S2352938525000564?via%3Dihub)

- Paper footprint attributes: [Springer](https://link.springer.com/article/10.1186/s40323-026-00323-y)

---

<!--header: ""-->

# [Thesis](https://github.com/MiguelUrenaPliego/MasterThesis/blob/main/thesis.pdf)

<div style="margin:auto;">
  <a href="https://github.com/MiguelUrenaPliego/MasterThesis/blob/main/thesis.pdf">
    <img
      src="figures/front_page.jpg"
      style="height:32%; object-fit:contain; display:block;"
    >
  </a>
</div>

---

<!-- _class: last two-line-logos -->

# Questions?
## Thank you!

<div style="flex: 1; font-size: 1em; margin-top:-15rem">

Miguel Ureña Pliego

Contact: 
miguel.urena@alumnos.upm.es

Github: [MiguelUrenaPliego](https://github.com/MiguelUrenaPliego)
LinkedIn: [miguel-urena-pliego](www.linkedin.com/in/miguel-urena-pliego)

</div>