# Green Cover Calculator — Step-by-Step User Guide

**Version:** 1.3.0 | **Author:** Arun Kumar Pandey

> This guide walks you through everything from a blank machine to a fully running
> analysis with real satellite data — in order, step by step. No prior knowledge
> of the codebase is assumed.

---

## Table of Contents

- [Part A — First-Time Setup](#part-a--first-time-setup)
  - [Step 1 — Check Python version](#step-1--check-python-version)
  - [Step 2 — Get the project files](#step-2--get-the-project-files)
  - [Step 3 — Create a virtual environment](#step-3--create-a-virtual-environment)
  - [Step 4 — Install dependencies](#step-4--install-dependencies)
  - [Step 5 — Verify the installation](#step-5--verify-the-installation)
- [Part B — Test with Synthetic Data First](#part-b--test-with-synthetic-data-first)
  - [Step 6 — Run the examples script](#step-6--run-the-examples-script)
  - [Step 7 — Check the outputs](#step-7--check-the-outputs)
- [Part C — Getting Real Satellite Data](#part-c--getting-real-satellite-data)
  - [Step 8 — Download Landsat data (USGS)](#step-8--download-landsat-data-usgs)
  - [Step 9 — Download Sentinel-2 data (Copernicus)](#step-9--download-sentinel-2-data-copernicus)
  - [Step 10 — Organise your data files](#step-10--organise-your-data-files)
- [Part D — Configure and Run](#part-d--configure-and-run)
  - [Step 11 — Edit config.yaml](#step-11--edit-configyaml)
  - [Step 12 — Run the analysis](#step-12--run-the-analysis)
  - [Step 13 — Understand the console output](#step-13--understand-the-console-output)
  - [Step 14 — Find and understand the outputs](#step-14--find-and-understand-the-outputs)
- [Part E — Common Use Cases](#part-e--common-use-cases)
  - [Use Case 1 — Single scene, one location](#use-case-1--single-scene-one-location)
  - [Use Case 2 — Time series of one location](#use-case-2--time-series-of-one-location)
  - [Use Case 3 — Multiple locations in one run](#use-case-3--multiple-locations-in-one-run)
  - [Use Case 4 — Sentinel-2 high-resolution analysis](#use-case-4--sentinel-2-high-resolution-analysis)
  - [Use Case 5 — Minimal run (NDVI only, no SWIR/blue)](#use-case-5--minimal-run-ndvi-only-no-swirblue)
- [Part F — Where to Change What](#part-f--where-to-change-what)
  - [F.1 Analysis parameters](#f1-analysis-parameters)
  - [F.2 Output and chart settings](#f2-output-and-chart-settings)
  - [F.3 Vegetation class boundaries](#f3-vegetation-class-boundaries)
  - [F.4 Index formula coefficients](#f4-index-formula-coefficients)
  - [F.5 Sensor scaling constants](#f5-sensor-scaling-constants)
  - [F.6 File and folder locations](#f6-file-and-folder-locations)
- [Part G — Troubleshooting](#part-g--troubleshooting)

---

## Part A — First-Time Setup

### Step 1 — Check Python version

Open a terminal (macOS/Linux) or Command Prompt / PowerShell (Windows) and run:

```bash
python --version
```

You need **Python 3.10 or later**. If you see `3.9.x` or lower:

- **macOS/Linux:** Install via [pyenv](https://github.com/pyenv/pyenv) or download from [python.org](https://python.org)
- **Windows:** Download the installer from [python.org](https://python.org) and check "Add Python to PATH"
- **Anaconda users:** `conda create -n greencover python=3.11 && conda activate greencover`

---

### Step 2 — Get the project files

Your project directory should look exactly like this before you start:

```
Green_cover_project/
├── main.py
├── examples.py
├── config.yaml
├── requirements.txt
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── sensor_config.py
│   ├── data_loader.py
│   ├── ndvi_calculator.py
│   ├── visualization.py
│   └── scientific_visualization.py
├── data/           ← you will put satellite files here (currently empty)
└── output/         ← will be auto-created when you run
```

> If the `data/` and `output/` folders do not exist, create them:
> ```bash
> mkdir -p data/landsat data/sentinel2
> ```

---

### Step 3 — Create a virtual environment

It is strongly recommended to use a virtual environment to keep dependencies isolated.

```bash
# Navigate into the project folder first
cd Green_cover_project

# Create the virtual environment
python -m venv .venv

# Activate it
# macOS / Linux:
source .venv/bin/activate

# Windows (Command Prompt):
.venv\Scripts\activate.bat

# Windows (PowerShell):
.venv\Scripts\Activate.ps1
```

Your terminal prompt should now show `(.venv)` at the start. All following commands assume the environment is active.

---

### Step 4 — Install dependencies

```bash
pip install -r requirements.txt
```

This installs: `numpy`, `scipy`, `matplotlib`, `pyyaml`, and `rasterio`.

**If rasterio fails on Windows**, use conda instead:

```bash
conda install -c conda-forge rasterio
pip install numpy scipy matplotlib pyyaml
```

**If rasterio fails on Linux** with GDAL errors:

```bash
sudo apt-get install libgdal-dev
pip install rasterio
```

**Expected output when successful:**

```
Successfully installed matplotlib-3.8.2 numpy-1.26.3 pyyaml-6.0.1
rasterio-1.3.9 scipy-1.12.0
```

---

### Step 5 — Verify the installation

```bash
python -c "
import numpy, scipy, matplotlib, yaml, rasterio
print('numpy    :', numpy.__version__)
print('scipy    :', scipy.__version__)
print('matplotlib:', matplotlib.__version__)
print('pyyaml   :', yaml.__version__)
print('rasterio :', rasterio.__version__)
print()
print('All dependencies installed correctly.')
"
```

If any import raises `ModuleNotFoundError`, re-run the install for that specific package:

```bash
pip install <package-name>
```

---

## Part B — Test with Synthetic Data First

Before touching any real satellite files, run the examples script. It uses internally generated fake data so nothing needs to be downloaded. This confirms that all modules load correctly and charts can be saved.

### Step 6 — Run the examples script

```bash
python examples.py
```

This runs six self-contained demonstrations:

| Example | What it does |
|---|---|
| Example 1 | Calculates NDVI statistics and prints them |
| Example 2 | Calculates green cover at four different thresholds |
| Example 3 | Classifies pixels into vegetation categories |
| Example 4 | Calculates EVI and compares its mean to NDVI |
| Example 5 | Computes area statistics at 30 m resolution |
| Example 6 | Creates and saves four PNG chart files |

**Expected terminal output (abbreviated):**

```
10:15:23  INFO  — ============================================================
10:15:23  INFO  — Example 1: Basic NDVI Calculation
10:15:23  INFO  — ============================================================
10:15:23  INFO  — NDVI Statistics:
10:15:23  INFO  —   Mean:      0.2341
10:15:23  INFO  —   Median:    0.2298
...
10:15:24  INFO  — All examples completed.
```

---

### Step 7 — Check the outputs

After `examples.py` finishes, check that chart files were created:

```
output/
└── examples/
    ├── example_ndvi.png
    ├── example_classification.png
    ├── example_statistics.png
    └── example_rgb.png
```

Open any of these PNGs to confirm they look like maps and charts. If this works, your entire Python environment and the `src/` package are functioning correctly.

> **If you see errors in this step** — stop here and fix them before proceeding to real data. The most common causes are a missing package (re-run `pip install -r requirements.txt`) or an import error in `src/` (check you are running from the project root, not from inside `src/`).

---

## Part C — Getting Real Satellite Data

### Step 8 — Download Landsat data (USGS)

**Portal:** [https://earthexplorer.usgs.gov](https://earthexplorer.usgs.gov)

1. Create a free USGS EarthExplorer account if you do not have one
2. In the **Search Criteria** tab, draw your area of interest on the map or enter coordinates
3. Set your date range under **Date Range**
4. In the **Data Sets** tab, expand **Landsat** → **Landsat Collection 2 Level-2** → tick **Landsat 8-9 OLI/TIRS C2 L2**
5. Click **Results**
6. For each scene you want, click the download icon → choose **Product Options** → download **Bundle** (all bands) or individual band files

**Which files to download** (from the bundle, keep only):

| File to keep | Band | What it contains |
|---|---|---|
| `*_SR_B2.TIF` | Blue | Needed for EVI |
| `*_SR_B4.TIF` | Red | **Required** |
| `*_SR_B5.TIF` | NIR | **Required** |
| `*_SR_B6.TIF` | SWIR-1 | Needed for NDWI |

You can delete all other band files (`B1`, `B3`, `B7`, `B10`, `B11`, `QA` files etc.) to save disk space. A typical Landsat scene is ~1 GB total but the four bands above together are about 200 MB.

**Scene naming convention:**
```
LC08_L2SP_146040_20240115_20240122_02_T1_SR_B4.TIF
 ↑    ↑    ↑      ↑        ↑        ↑  ↑   ↑  ↑
 |    |    |      |        |        |  |   |  Band
 |    |    |      |        |        |  |   Product
 |    |    |      |        |        |  Tier
 |    |    |      |        |        Collection
 |    |    |      |        Processing date
 |    |    |      Acquisition date
 |    |    Path/Row
 |    Processing level
 Sensor (08=Landsat 8, 09=Landsat 9)
```

---

### Step 9 — Download Sentinel-2 data (Copernicus)

**Portal:** [https://dataspace.copernicus.eu](https://dataspace.copernicus.eu)

1. Create a free Copernicus account
2. Use the search tool to draw your area of interest
3. Filter by **Product Type: S2MSI2A** (Level-2A, atmospherically corrected)
4. Filter by cloud cover — aim for less than 10% if possible
5. Download the `.SAFE` folder for your chosen scene

**Inside the `.SAFE` folder, navigate to:**
```
GRANULE/
└── L2A_T43PGQ_A.../
    └── IMG_DATA/
        ├── R10m/
        │   ├── *_B02_10m.jp2    ← Blue
        │   ├── *_B04_10m.jp2    ← Red  (Required)
        │   └── *_B08_10m.jp2    ← NIR  (Required)
        └── R20m/
            └── *_B11_20m.jp2    ← SWIR (for NDWI)
```

> **Important about B11 (SWIR):** It is 20 m resolution while B02/B04/B08 are 10 m. If you want to use NDWI with Sentinel-2, you must resample B11 to 10 m first using this command:
> ```bash
> gdalwarp -tr 10 10 -r bilinear \
>     T43PGQ_20240220_B11_20m.jp2 \
>     T43PGQ_20240220_B11_10m.jp2
> ```
> Then reference the `_10m.jp2` file in `config.yaml`. If you skip NDWI, you do not need B11 at all.

---

### Step 10 — Organise your data files

Move or copy your downloaded files into the `data/` directory:

```
Green_cover_project/
└── data/
    ├── landsat/
    │   ├── LC08_L2SP_146040_20231115_SR_B2.TIF
    │   ├── LC08_L2SP_146040_20231115_SR_B4.TIF
    │   ├── LC08_L2SP_146040_20231115_SR_B5.TIF
    │   ├── LC08_L2SP_146040_20231115_SR_B6.TIF
    │   ├── LC08_L2SP_146040_20240315_SR_B2.TIF
    │   ├── LC08_L2SP_146040_20240315_SR_B4.TIF
    │   ├── LC08_L2SP_146040_20240315_SR_B5.TIF
    │   └── LC08_L2SP_146040_20240315_SR_B6.TIF
    └── sentinel2/
        ├── T43PGQ_20240220_B02_10m.jp2
        ├── T43PGQ_20240220_B04_10m.jp2
        ├── T43PGQ_20240220_B08_10m.jp2
        └── T43PGQ_20240220_B11_10m.jp2  ← resampled from 20m
```

File names can be anything — the tool does not parse filenames. You just need to reference the correct path in `config.yaml` in the next step.

---

## Part D — Configure and Run

### Step 11 — Edit config.yaml

Open `config.yaml` in any text editor. This is **the only file you need to edit** for a normal analysis run.

The file has three sections. Here is a complete annotated example:

```yaml
# ─── Section 1: Output settings ───────────────────────────────────────────────
output:
  directory: "output"              # Where all outputs are saved.
                                   # Relative to project root, or use an absolute path.
                                   # The folder is auto-created if it does not exist.

  save_reports: true               # true = write a text summary file per scene
  save_visualizations: true        # true = save basic PNG charts (NDVI map, classification, etc.)
  save_scientific_charts: true     # true = save advanced scientific PNGs
  scientific_subdirectory: "scientific"   # Subfolder inside output/ for scientific charts
  dpi: 300                         # Resolution of saved figures. 300 = print quality.
                                   # Use 150 for faster saving / smaller files.

# ─── Section 2: Analysis parameters ───────────────────────────────────────────
analysis:
  ndvi_threshold: 0.4      # Pixels with NDVI >= this are counted as "green".
                           # 0.4 is appropriate for moderate-to-dense vegetation.
                           # Lower to 0.2 to include sparse dryland vegetation.
                           # Raise to 0.6 to count only dense canopy.

  savi_L: 0.5              # Soil brightness correction for SAVI index.
                           # 0.5 = mixed vegetation/soil (default, works for most scenes).
                           # 0.25 = dense vegetation (forest scenes).
                           # 1.0 = very sparse vegetation / mostly bare soil.

  change_gain_threshold:  0.10   # ΔNDVI ≥ +0.10 = vegetation GAIN between two dates.
  change_loss_threshold: -0.10   # ΔNDVI ≤ -0.10 = vegetation LOSS between two dates.
                                 # Tighten to ±0.05 for more sensitive detection.
                                 # Loosen to ±0.15 for noisy or coarse data.

  spatial_cv_window: 15    # Size (in pixels) of the sliding window for the
                           # spatial variability (CV) map.
                           # Larger = smoother map, less spatial detail.
                           # Range: 5–50. 15 is a good default.

# ─── Section 3: Scenes ────────────────────────────────────────────────────────
scenes:

  - sensor: landsat8                         # Must be: landsat8, landsat9, or sentinel2
    location: "Delhi NCR"                    # Any descriptive name you choose.
                                             # IMPORTANT: scenes with the SAME location
                                             # string are grouped as a time series.
    date: "2023-11-15"                       # Acquisition date. Format: YYYY-MM-DD.
                                             # Used for labelling charts and reports only.
    bands:
      red:  "data/landsat/LC08_..._B4.TIF"  # Path to red band file. REQUIRED.
      nir:  "data/landsat/LC08_..._B5.TIF"  # Path to NIR band file. REQUIRED.
      blue: "data/landsat/LC08_..._B2.TIF"  # OPTIONAL. Enables EVI and RGB overlay.
                                             # Remove this line entirely to skip EVI.
      swir: "data/landsat/LC08_..._B6.TIF"  # OPTIONAL. Enables NDWI (water stress).
                                             # Remove this line entirely to skip NDWI.
```

**The most important rule about `location:`**

Two scenes are treated as a **time series** if and only if their `location:` values are identical strings. Capitalisation and spaces matter.

```yaml
# These TWO will be grouped as a time series (same string):
- location: "Delhi NCR"
  date: "2023-11-15"

- location: "Delhi NCR"
  date: "2024-03-15"

# This one will NOT be grouped with either of the above:
- location: "delhi ncr"    ← different capitalisation = treated as separate location
```

---

### Step 12 — Run the analysis

From the project root directory (where `main.py` lives):

```bash
python main.py
```

To use a different config file (useful when you have multiple study areas):

```bash
python main.py --config path/to/my_other_config.yaml
```

That is all. The tool reads the config, processes every scene in order, runs temporal analysis automatically for any location with 2+ scenes, saves all outputs, and exits.

---

### Step 13 — Understand the console output

The tool prints structured log messages. Here is what each part means:

```
2024-01-15 10:23:01  INFO  __main__ — Config loaded: config.yaml  (2 scene(s))
                                      ↑ number of scenes found in config.yaml

════════════════════════════════════════════════════
Scene: Delhi NCR (2023-11-15)  sensor=landsat8
════════════════════════════════════════════════════

Step 1 — Loading bands …
  red    shape=(7581, 7711)  nodata-masked=142300 px
         ↑ image dimensions  ↑ number of masked (invalid) pixels

Step 2 — Calculating vegetation indices …
  NDVI  shape=(7581, 7711)  mean=0.2841  range=[-0.1832, 0.8923]  valid_px=7247441
                                         ↑ typical range for a mixed urban/veg scene

Step 3 — Green cover …
  Green cover: 31.42%       ← % of valid pixels with NDVI ≥ 0.4

Step 4 — Classifying vegetation …
  Water:                    2.14%
  Bare Soil:                18.33%
  Sparse Vegetation:        48.11%
  Moderate Vegetation:      24.18%
  Dense Vegetation:          7.24%

Step 5 — Area statistics (30 m/pixel) …
  Total=6524.70 km²   Green=2050.36 km²

Step 6 — Basic visualisations …
  3 basic figure(s) saved.

Step 7 — Scientific visualisations …
  ✓  Delhi_NCR_2023-11-15_ndvi_histogram.png
  ✓  Delhi_NCR_2023-11-15_index_boxplot.png
  ...

Step 8 — Writing report …
  Report → output/report_Delhi_NCR

── Temporal analysis: Delhi NCR  (2 scenes) ──
  Change 2023-11-15→2024-03-15: loss=12.3%  stable=71.4%  gain=16.3%
```

**Warning signs to watch for:**

| Message | What it means | What to do |
|---|---|---|
| `Band file not found: data/...` | Path in config.yaml is wrong | Check the path, filename, and extension |
| `Band shape mismatch` | Two band files have different dimensions | Confirm you downloaded matching bands from the same scene |
| `nodata-masked=0 px` with very high values | Scaling may have failed | Confirm you are using Level-2 SR product, not Level-1 TOA |
| `nodata-masked` = nearly all pixels | Wrong NoData value | Check if your sensor uses a different fill value |
| `NDVI mean > 0.8` | Likely a forest-only subscene | Normal — not an error |
| `NDVI mean < 0.05` | Likely urban / desert / cloud | Normal if expected for scene |

---

### Step 14 — Find and understand the outputs

After a successful run, the `output/` directory contains:

```
output/
│
├── Delhi_NCR_2023-11-15_ndvi.png          ← Spatial NDVI map (RdYlGn colormap)
├── Delhi_NCR_2023-11-15_classification.png ← Land cover classes map
├── Delhi_NCR_2023-11-15_stats.png         ← Bar chart: mean/median/min/max/std
├── Delhi_NCR_2023-11-15_evi.png           ← EVI map (if blue band provided)
│
├── report_Delhi_NCR/
│   └── summary.txt                        ← Text file: all stats in plain text
│
├── analysis_results.json                  ← Machine-readable results for all scenes
│
└── scientific/
    ├── Delhi_NCR_2023-11-15_ndvi_histogram.png   ← Distribution + KDE
    ├── Delhi_NCR_2023-11-15_band_correlation.png  ← Red vs NIR scatter (quality check)
    ├── Delhi_NCR_2023-11-15_index_boxplot.png     ← All indices side by side
    ├── Delhi_NCR_2023-11-15_index_comparison.png  ← Spatial maps of all indices
    ├── Delhi_NCR_2023-11-15_feature_space.png     ← NIR vs Red endmember diagram
    ├── Delhi_NCR_2023-11-15_ndvi_vs_evi.png       ← NDVI vs EVI scatter
    ├── Delhi_NCR_2023-11-15_rgb_ndvi_overlay.png  ← RGB + vegetation highlighted
    ├── Delhi_NCR_2023-11-15_spatial_cv.png        ← Fragmentation/variability map
    │
    │   ─── temporal charts (only when ≥ 2 scenes of same location) ───
    │
    ├── Delhi_NCR_ndvi_timeseries.png              ← Mean NDVI over time
    ├── Delhi_NCR_2023-11-15_to_2024-03-15_change.png  ← Change detection (4-panel)
    ├── Delhi_NCR_phenology_heatmap.png            ← Class × date NDVI matrix
    └── Delhi_NCR_greencover_timeseries.png        ← Green cover % over time
```

The `analysis_results.json` file is a structured record of all scene statistics, useful for importing into Excel, pandas, or another script:

```json
[
  {
    "location": "Delhi NCR",
    "date": "2023-11-15",
    "green_cover_percentage": 31.42,
    "ndvi_statistics": {
      "mean": 0.2841,
      "std": 0.1923,
      ...
    },
    "vegetation_classification": {
      "water": 2.14,
      "bare_soil": 18.33,
      ...
    }
  }
]
```

---

## Part E — Common Use Cases

### Use Case 1 — Single scene, one location

The simplest case. One scene, one location, no temporal analysis.

```yaml
scenes:
  - sensor: landsat8
    location: "Pune City"
    date: "2024-06-01"
    bands:
      red:  "data/landsat/LC08_..._B4.TIF"
      nir:  "data/landsat/LC08_..._B5.TIF"
      blue: "data/landsat/LC08_..._B2.TIF"
      swir: "data/landsat/LC08_..._B6.TIF"
```

**Outputs produced:** All basic and scientific charts for the single scene. No temporal charts (need at least 2 scenes for those).

---

### Use Case 2 — Time series of one location

Add multiple scenes with the **exact same** `location:` string. They are automatically sorted by date and processed as a series.

```yaml
scenes:
  - sensor: landsat8
    location: "Bangalore Forest"
    date: "2023-01-10"
    bands:
      red:  "data/landsat/LC08_..._20230110_B4.TIF"
      nir:  "data/landsat/LC08_..._20230110_B5.TIF"
      blue: "data/landsat/LC08_..._20230110_B2.TIF"

  - sensor: landsat8
    location: "Bangalore Forest"        # ← same string, grouped automatically
    date: "2023-05-15"
    bands:
      red:  "data/landsat/LC08_..._20230515_B4.TIF"
      nir:  "data/landsat/LC08_..._20230515_B5.TIF"
      blue: "data/landsat/LC08_..._20230515_B2.TIF"

  - sensor: landsat8
    location: "Bangalore Forest"        # ← third scene, enables phenology heatmap
    date: "2023-10-20"
    bands:
      red:  "data/landsat/LC08_..._20231020_B4.TIF"
      nir:  "data/landsat/LC08_..._20231020_B5.TIF"
      blue: "data/landsat/LC08_..._20231020_B2.TIF"
```

**Outputs produced:** All per-scene charts plus:
- `Bangalore_Forest_ndvi_timeseries.png`
- `Bangalore_Forest_2023-01-10_to_2023-05-15_change.png`
- `Bangalore_Forest_2023-05-15_to_2023-10-20_change.png`
- `Bangalore_Forest_phenology_heatmap.png` (needs ≥ 3 scenes)
- `Bangalore_Forest_greencover_timeseries.png`

---

### Use Case 3 — Multiple locations in one run

Different `location:` strings are processed independently. Useful for comparing cities or regions.

```yaml
scenes:
  - sensor: landsat8
    location: "Mumbai"
    date: "2024-01-15"
    bands:
      red: "data/landsat/mumbai_B4.TIF"
      nir: "data/landsat/mumbai_B5.TIF"

  - sensor: landsat8
    location: "Chennai"
    date: "2024-01-18"
    bands:
      red: "data/landsat/chennai_B4.TIF"
      nir: "data/landsat/chennai_B5.TIF"

  - sensor: sentinel2
    location: "Hyderabad"
    date: "2024-01-20"
    bands:
      red: "data/sentinel2/hyd_B04_10m.jp2"
      nir: "data/sentinel2/hyd_B08_10m.jp2"
```

**Outputs produced:** Separate chart sets for Mumbai, Chennai, and Hyderabad. No temporal charts because each location has only one scene.

---

### Use Case 4 — Sentinel-2 high-resolution analysis

Sentinel-2 works exactly like Landsat — just use `sensor: sentinel2` and point to `.jp2` files. The tool automatically applies the correct scaling ($M_\rho = 1 \times 10^{-4}$) and uses 10 m as the pixel size for area calculations.

```yaml
scenes:
  - sensor: sentinel2
    location: "Aravalli Ridge"
    date: "2024-02-20"
    bands:
      red:  "data/sentinel2/T43RGQ_20240220_B04_10m.jp2"
      nir:  "data/sentinel2/T43RGQ_20240220_B08_10m.jp2"
      blue: "data/sentinel2/T43RGQ_20240220_B02_10m.jp2"
      swir: "data/sentinel2/T43RGQ_20240220_B11_10m.jp2"   # must be resampled to 10m
```

> Note that Sentinel-2 scenes at 10 m resolution are ~10× larger in pixel count than Landsat at 30 m for the same area. The `band_correlation` and `feature_space` charts automatically subsample to 200,000 pixels for speed when the scene is large.

---

### Use Case 5 — Minimal run (NDVI only, no SWIR/blue)

If you only have red and NIR bands (or want the fastest possible run), simply omit `blue:` and `swir:` from the scene. The tool will skip EVI, NDWI, and RGB overlay but everything else will still work.

```yaml
scenes:
  - sensor: landsat8
    location: "Quick Test"
    date: "2024-03-01"
    bands:
      red: "data/landsat/..._B4.TIF"    # required
      nir: "data/landsat/..._B5.TIF"    # required
      # blue and swir lines simply absent — no error, those indices are skipped
```

---

## Part F — Where to Change What

This section is a direct map: **what you want to change → which file → which line**.

---

### F.1 Analysis parameters

All of these are in **`config.yaml`** under the `analysis:` block. This is the first place to look for any tuning.

| What to change | Key in `config.yaml` | Notes |
|---|---|---|
| Green cover threshold | `analysis.ndvi_threshold` | Default `0.4`. Range: `0.2`–`0.6` |
| SAVI soil correction factor | `analysis.savi_L` | Default `0.5`. See §6.3 of DOCUMENTATION.md |
| Change detection sensitivity | `analysis.change_gain_threshold` and `analysis.change_loss_threshold` | Default `±0.10` |
| Spatial variability window size | `analysis.spatial_cv_window` | Default `15` pixels |
| Pixel size for area calculation | `pixel_size_m:` inside each scene block | Overrides sensor default for that scene only |

**Example — make green cover stricter (only dense forest):**

```yaml
analysis:
  ndvi_threshold: 0.6    # was 0.4
```

**Example — more sensitive change detection:**

```yaml
analysis:
  change_gain_threshold:  0.05   # was  0.10
  change_loss_threshold: -0.05   # was -0.10
```

---

### F.2 Output and chart settings

All in **`config.yaml`** under the `output:` block.

| What to change | Key | Notes |
|---|---|---|
| Output folder location | `output.directory` | Can be absolute path |
| Scientific charts subfolder | `output.scientific_subdirectory` | Default: `"scientific"` |
| Turn off basic charts | `output.save_visualizations: false` | Saves time on large scenes |
| Turn off scientific charts | `output.save_scientific_charts: false` | Saves time on large scenes |
| Turn off text reports | `output.save_reports: false` | |
| Figure resolution | `output.dpi` | Default `300`. Use `150` for faster saves |

**Example — only save scientific charts, no basic charts or reports:**

```yaml
output:
  save_reports: false
  save_visualizations: false
  save_scientific_charts: true
```

---

### F.3 Vegetation class boundaries

**File:** `src/config.py` — the `VEGETATION_CLASSES` dictionary.

```python
# Current defaults:
VEGETATION_CLASSES: dict[str, tuple[float, float]] = {
    "water":               (-1.0,  0.0),
    "bare_soil":           ( 0.0,  0.2),
    "sparse_vegetation":   ( 0.2,  0.4),
    "moderate_vegetation": ( 0.4,  0.6),
    "dense_vegetation":    ( 0.6,  1.0),
}
```

**Example — split dense vegetation into two sub-classes:**

```python
VEGETATION_CLASSES = {
    "water":               (-1.0,  0.0),
    "bare_soil":           ( 0.0,  0.2),
    "sparse_vegetation":   ( 0.2,  0.4),
    "moderate_vegetation": ( 0.4,  0.6),
    "dense_vegetation":    ( 0.6,  0.8),
    "very_dense_vegetation":(0.8,  1.0),   # ← new class
}
```

> **After changing class boundaries**, also update the `lo_hi` lists in these three methods in `src/scientific_visualization.py`:
> - `plot_phenology_heatmap()` — line starting with `lo_hi = [(-1, 0), (0, .2)...`
> - `plot_ndvi_timeseries()` — line starting with `lo_hi = [(-1, 0), (0, .2)...`
> - `plot_green_cover_timeseries()` — line starting with `lo_hi_names = [(0.2, 0.4...`

---

### F.4 Index formula coefficients

**File:** `src/config.py`

These are the EVI formula constants. The MODIS standard values are correct for Landsat and Sentinel-2 and should only be changed for non-standard sensors.

```python
EVI_GAIN: float = 2.5    # gain factor G
EVI_C1:   float = 6.0    # red aerosol correction coefficient
EVI_C2:   float = 7.5    # blue aerosol correction coefficient
```

The SAVI `L` factor is **not** here — it is in `config.yaml` under `analysis.savi_L` so you can change it without touching source code.

---

### F.5 Sensor scaling constants

**File:** `src/sensor_config.py`

These values come from official product documentation and should not normally need to change. Edit only if:
- You are adding a new sensor
- USGS or ESA publishes a correction to the scaling coefficients

```python
_LANDSAT_PROFILE = SensorProfile(
    reflectance_scale=2.75e-5,   # ← from USGS Collection-2 guide
    reflectance_offset=-0.2,     # ← from USGS Collection-2 guide
    nodata_value=0.0,
    valid_min=1,
    valid_max=65455,
    default_pixel_size_m=30.0,
)

_SENTINEL2_PROFILE = SensorProfile(
    reflectance_scale=1e-4,      # ← from ESA Level-2A spec
    reflectance_offset=0.0,
    nodata_value=0.0,
    valid_min=1,
    valid_max=10000,
    default_pixel_size_m=10.0,
)
```

**To add a completely new sensor:**

```python
SENSOR_PROFILES["my_sensor"] = SensorProfile(
    name="My Sensor Level-2",
    reflectance_scale=1e-4,       # from your sensor's product guide
    reflectance_offset=0.0,
    nodata_value=0.0,
    valid_min=1,
    valid_max=10000,
    default_pixel_size_m=20.0,
    supported_extensions=(".tif",),
)
```

Then in `config.yaml`, use `sensor: my_sensor`.

---

### F.6 File and folder locations

**File:** `src/config.py`

```python
ROOT_DIR  = Path(__file__).resolve().parent.parent   # project root
DATA_DIR  = ROOT_DIR / "data"                        # default data folder
OUTPUT_DIR= ROOT_DIR / "output"                      # default output folder
```

These are used as fallback defaults only. The actual paths used at runtime come from `config.yaml` (`output.directory`) and from the band paths in each scene block. You rarely need to change these.

---

## Part G — Troubleshooting

**`ModuleNotFoundError: No module named 'src'`**

You are running Python from the wrong directory. Always run from the project root:
```bash
cd Green_cover_project
python main.py
```

**`FileNotFoundError: Band file not found: data/landsat/...`**

The file path in `config.yaml` does not match the actual file. Check:
1. Is the file actually in `data/landsat/`? (run `ls data/landsat/`)
2. Is the filename in `config.yaml` spelled exactly correctly, including capitalisation and extension (`.TIF` vs `.tif`)?
3. Are you running from the project root, not from inside `data/`?

**`ValueError: Band shape mismatch`**

The red and NIR band files have different dimensions. This happens when:
- You accidentally mixed bands from two different Landsat scenes (different path/row or date)
- You are using a Sentinel-2 SWIR band at 20 m without resampling to 10 m

Fix: Confirm all files are from the exact same scene. For Sentinel-2 SWIR, use `gdalwarp` to resample to 10 m (see Step 9).

**`ImportError: rasterio is required to read Sentinel-2 JP2 files`**

rasterio is not installed. Install it:
```bash
pip install rasterio
# or on Windows/conda:
conda install -c conda-forge rasterio
```

**`NDVI mean is 0.0 or NaN for all pixels`**

Almost always means wrong product level. You must use **Level-2 Surface Reflectance** products, not Level-1 Top-of-Atmosphere (TOA). Level-1 Landsat DNs range up to ~65535 and when multiplied by `2.75e-5` and offset by `-0.2` will give physically correct reflectance. If your DNs are small (0–255 scaled floats), you loaded a pre-processed product with different scaling — check the product documentation.

**Charts are generated but are all grey / featureless**

Usually means nearly all pixels are masked as NoData. Verify that your scene has actual land coverage and is not mostly ocean or outside the sensor swath. Also check that the QA band is not included by mistake.

**`scipy.stats.gaussian_kde` error in histogram**

Occurs if the NDVI array has fewer than 10 valid pixels (degenerate scene). Check your NoData masking — if `nodata-masked` in the log equals nearly all pixels, the file loaded correctly but the scene is mostly fill data.

**`plot_phenology_heatmap` does not appear in outputs**

This chart requires at least 3 scenes of the same location. If you only have 2 scenes, it is silently skipped. Add a third scene to generate it.

**`analysis_results.json` is empty or missing**

The output directory may not have been created. Check that `output.directory` in `config.yaml` is a writable path. The tool creates it automatically but cannot do so if it is on a read-only filesystem.

**Temporal charts not generated even though I have 2 scenes**

Check that the `location:` strings in `config.yaml` are **exactly identical** — same capitalisation, same spaces. `"Delhi NCR"` and `"Delhi ncr"` are treated as two different locations.