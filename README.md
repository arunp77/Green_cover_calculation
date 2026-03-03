# Green Cover Calculator — Technical Documentation

**Version:** 1.3.0  
**Author:** Arun Kumar Pandey  
**Language:** Python 3.10+  
**Purpose:** Satellite-based vegetation analysis using Landsat 8/9 and Sentinel-2 imagery

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Repository Structure](#2-repository-structure)
3. [Installation and Setup](#3-installation-and-setup)
4. [Data Sources](#4-data-sources)
5. [Radiometric Pre-processing](#5-radiometric-pre-processing)
6. [Vegetation Indices — Equations and Scientific Basis](#6-vegetation-indices--equations-and-scientific-basis)
7. [Vegetation Classification Algorithm](#7-vegetation-classification-algorithm)
8. [Change Detection Algorithm](#8-change-detection-algorithm)
9. [Statistical Methods](#9-statistical-methods)
10. [Visualisation Catalogue](#10-visualisation-catalogue)
11. [Configuration Reference](#11-configuration-reference)
12. [Running the Tool](#12-running-the-tool)
13. [Module and API Reference](#13-module-and-api-reference)
14. [Where to Change What](#14-where-to-change-what)
15. [Extending the Tool](#15-extending-the-tool)
16. [References](#16-references)

---

## 1. Project Overview

The Green Cover Calculator is a production-ready Python tool for quantifying vegetation cover and health from multispectral satellite imagery. It ingests Level-2 Surface Reflectance (SR) products from Landsat 8, Landsat 9, and Sentinel-2 and produces:

- Five vegetation indices per scene (NDVI, EVI, SAVI, MSAVI2, NDWI)
- Pixel-level land cover classification into five vegetation density classes
- Area statistics in km² at sensor-native resolution
- Twelve scientific visualisation types spanning statistical, multi-index, temporal, and geospatial categories
- Automated change detection and phenology analysis when multiple scenes of the same location are provided
- A JSON results database for downstream analysis

The tool is designed for general remote sensing research and is applicable to urban green cover monitoring, agricultural health assessment, and forest cover and deforestation studies.

---

## 2. Repository Structure

```
Green_cover_project/
│
├── main.py                    # Entry point — reads config.yaml, runs pipeline
├── examples.py                # Standalone demos using synthetic data only
├── config.yaml                # All user-configurable settings and scene paths
├── requirements.txt           # Python package dependencies
│
├── src/
│   ├── __init__.py            # Package public API — imports all public classes
│   ├── config.py              # Global constants (thresholds, EVI coefficients, paths)
│   ├── sensor_config.py       # Per-sensor scaling factors, NoData values, pixel sizes
│   ├── data_loader.py         # Band loading, radiometric scaling, NoData masking
│   ├── ndvi_calculator.py     # All vegetation index calculations + change detection
│   ├── visualization.py       # Basic charts (NDVI map, classification, stats bar)
│   └── scientific_visualization.py   # Advanced scientific charts (12 chart types)
│
├── data/                      # Input satellite band files (user-supplied)
│   ├── landsat/               # Landsat GeoTIFF files (.TIF)
│   └── sentinel2/             # Sentinel-2 JP2 files (.jp2)
│
└── output/                    # All generated outputs (auto-created)
    ├── *.png                  # Basic visualisation figures
    ├── report_*/              # Per-scene text summary reports
    ├── analysis_results.json  # Structured results database
    └── scientific/            # Advanced scientific figures
```

---

## 3. Installation and Setup

### 3.1 Python version requirement

Python 3.10 or later is required. The codebase uses `str | Path` union type hints and `match` patterns that are not available in earlier versions.

### 3.2 Install dependencies

```bash
pip install -r requirements.txt
```

The `requirements.txt` contains:

| Package | Version | Purpose |
|---|---|---|
| `numpy` | ≥ 1.24 | Array operations, all index maths |
| `scipy` | ≥ 1.11 | Kernel density estimation, spatial CV filter |
| `matplotlib` | ≥ 3.7 | All visualisations |
| `pyyaml` | ≥ 6.0 | Parsing `config.yaml` |
| `rasterio` | ≥ 1.3 | Reading GeoTIFF and JP2 satellite files |

> **Windows users:** rasterio is best installed via conda to avoid binary dependency issues:
> ```bash
> conda install -c conda-forge rasterio
> ```

### 3.3 Verify installation

```bash
python -c "import rasterio, numpy, scipy, matplotlib, yaml; print('All dependencies OK')"
```

---

## 4. Data Sources

### 4.1 Landsat 8 and Landsat 9 (USGS)

**Portal:** [https://earthexplorer.usgs.gov](https://earthexplorer.usgs.gov)

**Product to download:** Collection 2, Level-2 Science Product (surface reflectance)

Landsat provides 30 m resolution imagery with a 16-day revisit cycle. Collection 2 Level-2 applies atmospheric correction using the Land Surface Reflectance Code (LaSRC) to produce surface reflectance values.

**Required bands:**

| Band | Wavelength | Use in this tool | Filename pattern |
|---|---|---|---|
| Band 2 (Blue) | 0.452–0.512 µm | EVI, RGB composite | `*_B2.TIF` |
| Band 4 (Red) | 0.636–0.673 µm | All indices | `*_B4.TIF` |
| Band 5 (NIR) | 0.851–0.879 µm | All indices | `*_B5.TIF` |
| Band 6 (SWIR-1) | 1.566–1.651 µm | NDWI | `*_B6.TIF` |

**Filename example:**
```
LC08_L2SP_146040_20240115_20240122_02_T1_SR_B4.TIF
```

### 4.2 Sentinel-2 (ESA / Copernicus)

**Portal:** [https://dataspace.copernicus.eu](https://dataspace.copernicus.eu)

**Product to download:** Level-2A (surface reflectance, atmospherically corrected by Sen2Cor)

Sentinel-2 provides 10 m resolution for visible and NIR bands with a 5-day revisit cycle (combined constellation).

**Required bands:**

| Band | Wavelength | Native resolution | Use | Filename pattern |
|---|---|---|---|---|
| B02 (Blue) | 0.458–0.523 µm | 10 m | EVI, RGB | `*_B02_10m.jp2` |
| B04 (Red) | 0.650–0.680 µm | 10 m | All indices | `*_B04_10m.jp2` |
| B08 (NIR) | 0.785–0.900 µm | 10 m | All indices | `*_B08_10m.jp2` |
| B11 (SWIR-1) | 1.565–1.655 µm | 20 m | NDWI | `*_B11_20m.jp2` |

> **Note on B11:** Sentinel-2 SWIR (B11) is at 20 m resolution while the other bands are 10 m. If B11 shape differs from the other bands, a shape mismatch error will be raised. Resample B11 to 10 m using `gdalwarp` before use:
> ```bash
> gdalwarp -tr 10 10 -r bilinear input_B11_20m.jp2 output_B11_10m.jp2
> ```

### 4.3 Data directory layout expected by `config.yaml`

```
data/
├── landsat/
│   ├── LC08_L2SP_146040_20240115_B2.TIF
│   ├── LC08_L2SP_146040_20240115_B4.TIF
│   ├── LC08_L2SP_146040_20240115_B5.TIF
│   └── LC08_L2SP_146040_20240115_B6.TIF
└── sentinel2/
    ├── T43PGQ_20240220_B02_10m.jp2
    ├── T43PGQ_20240220_B04_10m.jp2
    ├── T43PGQ_20240220_B08_10m.jp2
    └── T43PGQ_20240220_B11_10m.jp2
```

---

## 5. Radiometric Pre-processing

### 5.1 Why raw DN values cannot be used directly

Satellite sensors record raw Digital Numbers (DNs) — integer values proportional to the voltage measured by the detector. These are not physically meaningful reflectance values and cannot be compared across dates, sensors, or geographic regions. All vegetation index calculations require physical surface reflectance in the range $[0, 1]$.

### 5.2 Linear reflectance scaling

The tool applies the standard linear transformation defined in each sensor's product specification:

$$\rho = DN \times M_\rho + A_\rho$$

where:
- $\rho$ = physical surface reflectance $\in [0, 1]$
- $DN$ = raw digital number (integer stored in the file)
- $M_\rho$ = multiplicative rescaling factor
- $A_\rho$ = additive rescaling factor (offset)

**Sensor-specific constants** (from `src/sensor_config.py`):

| Sensor | $M_\rho$ | $A_\rho$ | Valid DN range | NoData DN |
|---|---|---|---|---|
| Landsat 8/9 Collection-2 L2 SR | $2.75 \times 10^{-5}$ | $-0.2$ | $[1,\ 65455]$ | $0$ |
| Sentinel-2 Level-2A SR | $1.0 \times 10^{-4}$ | $0.0$ | $[1,\ 10000]$ | $0$ |

**Example (Landsat):** A raw DN of $20000$ becomes:

$$\rho = 20000 \times 2.75 \times 10^{-5} + (-0.2) = 0.55 - 0.2 = 0.35$$

A reflectance of $0.35$ in the NIR band is physically reasonable for moderate vegetation.

### 5.3 NoData masking

Pixels with DN equal to the NoData value (0 for both sensors) or outside the valid DN range are set to `NaN` before any computation. This propagates through all subsequent index calculations — any pixel that is masked in any band remains `NaN` in all output arrays.

The masking logic in `src/data_loader.py`:

```python
valid = (data != nodata_value) & (data >= valid_min) & (data <= valid_max)
result = np.full_like(data, np.nan)
result[valid] = data[valid] * scale + offset
result = np.clip(result, 0.0, 1.0)
result[~valid] = np.nan   # restore NaN after clip
```

The final `clip` to $[0, 1]$ handles rare saturated or anomalous pixels that pass the DN range check but produce slightly out-of-range reflectance after scaling.

### 5.4 Where to change scaling parameters

All scaling constants are in `src/sensor_config.py`. To support a new sensor, add a new `SensorProfile` instance to the `SENSOR_PROFILES` dictionary:

```python
SENSOR_PROFILES["my_sensor"] = SensorProfile(
    name="My Sensor L2 SR",
    reflectance_scale=1e-4,
    reflectance_offset=0.0,
    nodata_value=0.0,
    valid_min=1,
    valid_max=10000,
    default_pixel_size_m=30.0,
    supported_extensions=(".tif",),
)
```

Then reference it in `config.yaml` as `sensor: my_sensor`.

---

## 6. Vegetation Indices — Equations and Scientific Basis

All indices are computed in `src/ndvi_calculator.py` by the `NDVICalculator` class. All inputs must be physical reflectance values $\in [0, 1]$ after pre-processing.

### 6.1 NDVI — Normalized Difference Vegetation Index

**Equation:**

$$\text{NDVI} = \frac{\rho_\text{NIR} - \rho_\text{Red}}{\rho_\text{NIR} + \rho_\text{Red}}$$

**Range:** $[-1,\ 1]$

**Scientific basis:** Rouse et al. (1973) exploited the strong contrast between plant chlorophyll absorption in the red ($\approx 0.67\ \mu\text{m}$) and the structural leaf reflectance in the NIR ($\approx 0.8\ \mu\text{m}$). Healthy vegetation absorbs red light for photosynthesis and strongly reflects NIR due to internal leaf cellular structure (mesophyll scattering). This produces high NIR and low red reflectance, giving NDVI values typically in $[0.6,\ 0.9]$ for dense canopy.

**Interpretation:**

| NDVI range | Land cover |
|---|---|
| $[-1.0,\ 0.0)$ | Water bodies, snow |
| $[0.0,\ 0.2)$ | Bare soil, rock, built-up |
| $[0.2,\ 0.4)$ | Sparse or stressed vegetation |
| $[0.4,\ 0.6)$ | Moderate vegetation cover |
| $[0.6,\ 1.0]$ | Dense, healthy vegetation |

**Limitations:** NDVI saturates at high leaf area index (LAI > 3–4), making it insensitive to further increases in biomass. It is also sensitive to soil background reflectance and atmospheric aerosols.

**Code location:** `NDVICalculator.calculate_ndvi()`

---

### 6.2 EVI — Enhanced Vegetation Index

**Equation:**

$$\text{EVI} = G \cdot \frac{\rho_\text{NIR} - \rho_\text{Red}}{\rho_\text{NIR} + C_1 \cdot \rho_\text{Red} - C_2 \cdot \rho_\text{Blue} + L}$$

**Standard coefficients** (MODIS standard, stored in `src/config.py`):

| Parameter | Value | Role |
|---|---|---|
| $G$ (gain) | $2.5$ | Scales output to a comparable dynamic range to NDVI |
| $C_1$ | $6.0$ | Red band aerosol correction |
| $C_2$ | $7.5$ | Blue band aerosol correction |
| $L$ | $1.0$ | Canopy background adjustment (fixed in EVI formulation) |

**Scientific basis:** Developed by Huete et al. (1997, 2002) for the MODIS sensor. EVI was specifically designed to address two key NDVI deficiencies: atmospheric aerosol contamination (corrected by the blue band term) and canopy background soil brightness (corrected by the $L$ and $C_1$ terms). EVI does not saturate in dense tropical forests where NDVI plateaus.

**Requires:** Blue band. EVI is only computed when `blue:` is specified in `config.yaml`.

**Code location:** `NDVICalculator.calculate_evi()`

---

### 6.3 SAVI — Soil-Adjusted Vegetation Index

**Equation:**

$$\text{SAVI} = \frac{\rho_\text{NIR} - \rho_\text{Red}}{\rho_\text{NIR} + \rho_\text{Red} + L} \cdot (1 + L)$$

**Default:** $L = 0.5$ (configurable via `savi_L` in `config.yaml`)

**Scientific basis:** Huete (1988) demonstrated that bare soil reflectance systematically biases NDVI, particularly in arid and semi-arid regions where vegetation is sparse. The soil factor $L$ compensates for the first-order soil background variation. The term $(1 + L)$ in the numerator is a normalisation factor ensuring SAVI approximates NDVI when $L \to 0$.

**Choosing $L$:**

| $L$ value | Appropriate for |
|---|---|
| $L = 1.0$ | Very sparse vegetation, predominantly bare soil |
| $L = 0.5$ | Intermediate cover (default, suitable for most scenes) |
| $L = 0.25$ | Dense vegetation with little bare soil |
| $L = 0.0$ | Equivalent to NDVI (no soil correction) |

**Code location:** `NDVICalculator.calculate_savi()`, with $L$ controlled by `savi_L` in `config.yaml`

---

### 6.4 MSAVI2 — Modified Soil-Adjusted Vegetation Index

**Equation:**

$$\text{MSAVI2} = \frac{2 \cdot \rho_\text{NIR} + 1 - \sqrt{(2 \cdot \rho_\text{NIR} + 1)^2 - 8 \cdot (\rho_\text{NIR} - \rho_\text{Red})}}{2}$$

**Scientific basis:** Qi et al. (1994) derived MSAVI2 as a self-adjusting form of SAVI that eliminates the need to specify $L$ by embedding a dynamic correction factor. The soil-noise-reduction (SNR) factor adjusts automatically based on the local NIR and Red reflectance values. MSAVI2 is algebraically equivalent to SAVI with a per-pixel optimal $L$. It is particularly useful when a scene spans highly variable soil backgrounds.

**Notes:** Pixels where the expression under the square root is negative (which can occur at cloud edges or over water) are set to `NaN`. The fraction of such pixels is logged at `DEBUG` level.

**Code location:** `NDVICalculator.calculate_msavi2()`

---

### 6.5 NDWI — Normalized Difference Water Index (vegetation water content)

**Equation:**

$$\text{NDWI} = \frac{\rho_\text{NIR} - \rho_\text{SWIR}}{\rho_\text{NIR} + \rho_\text{SWIR}}$$

**Range:** $[-1,\ 1]$

**Scientific basis:** Gao (1996) showed that liquid water in plant canopies absorbs strongly in the shortwave infrared (SWIR, $1.57\ \mu\text{m}$) while reflecting strongly in the NIR. NDWI is therefore sensitive to vegetation canopy water content (CWC) and is used as a drought stress indicator. Positive values indicate high water content in healthy, well-irrigated vegetation. Decreasing NDWI over time in the same pixel indicates drying stress.

> **Do not confuse with McFeeters (1996) NDWI** which uses Green and NIR bands to detect open water bodies. This tool implements the Gao (1996) formulation for vegetation moisture.

**Requires:** SWIR band. Specify `swir:` in the scene's bands section in `config.yaml`.
- Landsat 8/9: `*_B6.TIF` (Band 6, SWIR-1)
- Sentinel-2: `*_B11_10m.jp2` (Band 11, resampled to 10 m)

**Code location:** `NDVICalculator.calculate_ndwi()`

---

### 6.6 Computing all indices in one call

```python
from src import NDVICalculator

calc = NDVICalculator(red_band, nir_band)
indices = calc.calculate_all_indices(
    blue_band=blue,   # enables EVI
    swir_band=swir,   # enables NDWI
    savi_L=0.5,
)
# indices = {"ndvi": ..., "savi": ..., "msavi2": ..., "evi": ..., "ndwi": ...}
```

---

## 7. Vegetation Classification Algorithm

### 7.1 NDVI threshold classification

Classification is performed in `GreenCoverAnalyzer.classify_vegetation()` using fixed NDVI boundary thresholds defined in `src/config.py`:

```python
VEGETATION_CLASSES = {
    "water":               (-1.0,  0.0),
    "bare_soil":           ( 0.0,  0.2),
    "sparse_vegetation":   ( 0.2,  0.4),
    "moderate_vegetation": ( 0.4,  0.6),
    "dense_vegetation":    ( 0.6,  1.0),
}
```

Each pixel $i$ is assigned class $k$ such that:

$$k_i = \arg\min_k \{ \text{NDVI}_i \in [\text{lower}_k,\ \text{upper}_k) \}$$

The upper bound of `dense_vegetation` uses inclusive comparison ($\leq 1.0$) to correctly classify pixels with NDVI exactly equal to 1.0. All class boundaries use half-open intervals $[\text{lower},\ \text{upper})$ to avoid double-counting.

### 7.2 Green cover percentage

Green cover $G$ is defined as the fraction of valid pixels with NDVI above a user-defined threshold $\tau$ (default $\tau = 0.4$, the lower bound of `moderate_vegetation`):

$$G = \frac{\sum_{i=1}^{N} \mathbf{1}[\text{NDVI}_i \geq \tau]}{\sum_{i=1}^{N} \mathbf{1}[\text{NDVI}_i \neq \text{NaN}]} \times 100\%$$

The threshold $\tau$ is set under `analysis.ndvi_threshold` in `config.yaml`.

### 7.3 Area calculation

For a scene with $N_\text{valid}$ valid pixels at ground sampling distance (GSD) $d$ metres:

$$A_\text{total} = N_\text{valid} \cdot \frac{d^2}{10^6} \quad [\text{km}^2]$$

$$A_\text{green} = N_\text{green} \cdot \frac{d^2}{10^6} \quad [\text{km}^2]$$

where $N_\text{green}$ is the count of pixels with NDVI $\geq 0.2$ (all vegetated classes). The pixel size $d$ defaults to the sensor's native resolution (30 m for Landsat, 10 m for Sentinel-2) and can be overridden per scene in `config.yaml` via `pixel_size_m`.

---

## 8. Change Detection Algorithm

### 8.1 NDVI differencing

The simplest and most widely used change detection method for vegetation is direct NDVI differencing (Singh, 1989):

$$\Delta\text{NDVI}_{i} = \text{NDVI}_{i,t_2} - \text{NDVI}_{i,t_1}$$

where $t_1$ is the earlier date and $t_2$ the later date. This produces a continuous change map:
- $\Delta\text{NDVI} > 0$: vegetation increase (recovery, growth, planting)
- $\Delta\text{NDVI} \approx 0$: no significant change
- $\Delta\text{NDVI} < 0$: vegetation decrease (deforestation, drought, urban expansion)

**Code location:** `GreenCoverAnalyzer.compute_ndvi_change()`

### 8.2 Change classification

The continuous $\Delta\text{NDVI}$ map is discretised into three classes using symmetric thresholds $\theta_\text{gain}$ and $\theta_\text{loss}$:

$$\text{class}_i = \begin{cases} \text{Loss}   & \Delta\text{NDVI}_i \leq \theta_\text{loss} \\ \text{Stable} & \theta_\text{loss} < \Delta\text{NDVI}_i < \theta_\text{gain} \\ \text{Gain}   & \Delta\text{NDVI}_i \geq \theta_\text{gain} \end{cases}$$

**Defaults** (configurable in `config.yaml` under `analysis`):
- $\theta_\text{gain} = +0.10$
- $\theta_\text{loss} = -0.10$

These values represent a 10% change in the normalised index, which typically corresponds to a detectable land cover transition at Landsat resolution. They can be tightened (e.g. $\pm 0.05$) for high-resolution Sentinel-2 data or loosened for noisier scenes.

**Code location:** `GreenCoverAnalyzer.classify_change()`

### 8.3 Temporal grouping

`main.py` automatically detects multi-temporal analysis by grouping all scenes with the same `location:` string from `config.yaml`. For each location with $n \geq 2$ scenes, change detection is run on every consecutive date pair (sorted chronologically). For $n$ scenes, this produces $n-1$ change maps.

---

## 9. Statistical Methods

### 9.1 NDVI descriptive statistics

Computed by `NDVICalculator.get_ndvi_statistics()` over all valid (non-NaN) pixels:

| Statistic | Formula | Interpretation |
|---|---|---|
| Mean $\bar{x}$ | $\frac{1}{N}\sum x_i$ | Average vegetation density |
| Standard deviation $\sigma$ | $\sqrt{\frac{1}{N}\sum(x_i - \bar{x})^2}$ | Scene heterogeneity |
| Minimum | $\min(x_i)$ | Least vegetated valid pixel |
| Maximum | $\max(x_i)$ | Most vegetated valid pixel |
| Median | $x_{[N/2]}$ | Robust central tendency (unaffected by outliers) |
| 25th percentile $P_{25}$ | $x_{[N/4]}$ | Lower quartile |
| 75th percentile $P_{75}$ | $x_{[3N/4]}$ | Upper quartile |

$P_{25}$ and $P_{75}$ are used for the interquartile range (IQR) in box plot visualisations.

### 9.2 Kernel Density Estimation (KDE)

The NDVI histogram overlays a non-parametric KDE using Gaussian kernels (implemented via `scipy.stats.gaussian_kde`). The bandwidth $h$ is selected using Scott's rule:

$$h = n^{-1/5} \cdot \hat{\sigma}$$

where $n$ is the number of valid pixels and $\hat{\sigma}$ is the standard deviation of the NDVI values. Scott's rule is the default in `scipy.stats.gaussian_kde` and is appropriate for unimodal and moderately skewed distributions. The KDE is evaluated at 500 equally spaced points across the observed NDVI range.

### 9.3 Pearson correlation coefficient

Band correlation plots compute the Pearson product-moment correlation between two reflectance bands:

$$r = \frac{\sum_{i=1}^N (x_i - \bar{x})(y_i - \bar{y})}{\sqrt{\sum_{i=1}^N (x_i - \bar{x})^2 \cdot \sum_{i=1}^N (y_i - \bar{y})^2}}$$

$r \in [-1, 1]$. For vegetation remote sensing, a high Red–NIR correlation ($r > 0.95$) after correct scaling indicates a well-mixed scene of soil and vegetation following the soil line. An unusually low correlation may indicate scaling errors, cloud contamination, or a strongly bimodal landscape.

### 9.4 Local coefficient of variation (spatial CV)

The spatial variability map computes the local coefficient of variation within a sliding window of size $w \times w$ pixels:

$$\text{CV}_{i,j} = \frac{\sigma_{w}(\text{NDVI}_{i,j})}{\left| \mu_{w}(\text{NDVI}_{i,j}) \right|}$$

where $\sigma_w$ and $\mu_w$ are the standard deviation and mean of the NDVI values within the $w \times w$ neighbourhood centred on pixel $(i, j)$. The filter is applied using `scipy.ndimage.generic_filter`.

High CV values indicate spatially heterogeneous patches — typically forest edges, riparian corridors, or fragmented urban green cover. Homogeneous dense canopy and uniform bare soil both produce low CV. The window size $w$ is controlled by `analysis.spatial_cv_window` in `config.yaml` (default: 15 pixels).

---

## 10. Visualisation Catalogue

All chart methods return a `str` path to the saved PNG file, or `None` if matplotlib is unavailable. Output DPI is 300 by default (set in `src/config.py` as `DEFAULT_DPI`).

### 10.1 Basic visualisations (`src/visualization.py`)

These are generated for every scene when `save_visualizations: true` in `config.yaml`.

| Method | Output file | Description |
|---|---|---|
| `plot_ndvi()` | `{location}_{date}_ndvi.png` | Spatial NDVI map with RdYlGn colormap, range $[-1, 1]$ |
| `plot_vegetation_classification()` | `{location}_{date}_classification.png` | Integer class map with categorical legend |
| `plot_statistics_summary()` | `{location}_{date}_stats.png` | Bar chart of mean, median, min, max, std |
| `plot_ndvi()` (EVI variant) | `{location}_{date}_evi.png` | Spatial EVI map with viridis colormap |
| `create_analysis_report()` | `report_{location}/summary.txt` | Text file with all statistics |

### 10.2 Scientific visualisations (`src/scientific_visualization.py`)

Generated when `save_scientific_charts: true`. Saved to `output/scientific/` by default.

#### Category 1: Statistical

| Method | Output file | Scientific purpose |
|---|---|---|
| `plot_ndvi_histogram()` | `*_ndvi_histogram.png` | Full NDVI distribution with KDE, class shading, mean/median lines. Bimodal peaks confirm vegetation–soil separation |
| `plot_band_correlation()` | `*_band_correlation.png` | Hexbin scatter of Red vs NIR (and Blue if available) with Pearson r. Radiometric quality check |
| `plot_index_boxplot()` | `*_index_boxplot.png` | Notched box plots for all computed indices. Compares spread and median across NDVI, EVI, SAVI, MSAVI2 |

#### Category 2: Multi-index comparison

| Method | Output file | Scientific purpose |
|---|---|---|
| `plot_index_comparison()` | `*_index_comparison.png` | Grid of spatial maps, one per index, same colour scale. Shows where indices diverge spatially |
| `plot_index_scatter()` | `*_ndvi_vs_evi.png` etc. | Scatter of two indices coloured by vegetation class. Reveals saturation and soil effects |
| `plot_vegetation_feature_space()` | `*_feature_space.png` | NIR vs Red reflectance diagram with soil line. Endmember identification |

#### Category 3: Temporal (requires ≥ 2 scenes of same location)

| Method | Min. scenes | Output file | Scientific purpose |
|---|---|---|---|
| `plot_ndvi_timeseries()` | 2 | `*_ndvi_timeseries.png` | Mean ± 1 std NDVI over time plus per-class means. Phenology and trend detection |
| `plot_change_detection()` | 2 | `*_T1_to_T2_change.png` | Four-panel: NDVI T1, T2, ΔNDVI map, change class map |
| `plot_phenology_heatmap()` | 3 | `*_phenology_heatmap.png` | Matrix of mean NDVI per class × date, annotated. Compact seasonal overview |
| `plot_green_cover_timeseries()` | 2 | `*_greencover_timeseries.png` | Total green cover % + stacked area by density class |

#### Category 4: Geospatial

| Method | Output file | Scientific purpose |
|---|---|---|
| `plot_rgb_ndvi_overlay()` | `*_rgb_ndvi_overlay.png` | True-colour RGB alongside RGB with vegetation highlighted green |
| `plot_zonal_stats()` | `*_zonal_stats.png` | NDVI statistics per user-defined zone with bar chart and zone map |
| `plot_spatial_variability()` | `*_spatial_cv.png` | Local CV map showing fragmentation and ecotones |

---

## 11. Configuration Reference

All user-facing settings are in `config.yaml`. This is the **only file you need to edit** for a new analysis.

```yaml
output:
  directory: "output"              # Root output folder
  save_reports: true               # Write text summary per scene
  save_visualizations: true        # Basic charts (visualization.py)
  save_scientific_charts: true     # Advanced charts (scientific_visualization.py)
  scientific_subdirectory: "scientific"   # Subfolder for advanced charts
  dpi: 300                         # Figure resolution (dots per inch)

analysis:
  ndvi_threshold: 0.4              # Green cover threshold; raise for denser-only
  savi_L: 0.5                      # SAVI soil factor; lower for denser vegetation
  change_gain_threshold:  0.10     # ΔNDVI ≥ this = vegetation gain
  change_loss_threshold: -0.10     # ΔNDVI ≤ this = vegetation loss
  spatial_cv_window: 15            # Sliding window size for CV map (pixels)

scenes:
  - sensor: landsat8               # "landsat8", "landsat9", or "sentinel2"
    location: "My Location"        # Human-readable name; same name = time series
    date: "2024-01-15"             # YYYY-MM-DD
    bands:
      red:  "data/landsat/..._B4.TIF"
      nir:  "data/landsat/..._B5.TIF"
      blue: "data/landsat/..._B2.TIF"   # optional, for EVI and RGB
      swir: "data/landsat/..._B6.TIF"   # optional, for NDWI
```

**Key rules:**
- Scenes with the same `location:` string are grouped automatically for temporal analysis
- Scenes are processed in the order listed; change detection pairs consecutive dates after sorting
- `blue:` and `swir:` are optional per-scene — omitting them disables EVI and NDWI respectively
- Band file paths can be absolute or relative to the project root

---

## 12. Running the Tool

### 12.1 Standard run (real data)

```bash
# From the project root
python main.py
```

Reads `config.yaml` in the project root by default.

### 12.2 Custom config file

```bash
python main.py --config /path/to/my_study_config.yaml
```

Useful when managing multiple study areas or time periods.

### 12.3 Synthetic data demos

```bash
python examples.py
```

Runs all six demonstration functions using generated synthetic data. No real satellite files are needed. This is purely for verifying that the pipeline runs correctly on your system. The synthetic data generator is in `SatelliteDataLoader.create_synthetic_data()`.

### 12.4 Expected console output

```
2024-01-15 10:23:01  INFO  __main__ — Config loaded: config.yaml  (2 scene(s))

════════════════════════════════════════════════════
Scene: Delhi NCR (2023-11-15)  sensor=landsat8
════════════════════════════════════════════════════
Step 1 — Loading bands …
  red    shape=(7581, 7711)  nodata-masked=142300 px
  nir    shape=(7581, 7711)  nodata-masked=142300 px
  blue   shape=(7581, 7711)  nodata-masked=142300 px
Step 2 — Calculating vegetation indices …
  NDVI  shape=(7581, 7711)  mean=0.2841  range=[-0.1832, 0.8923]  valid_px=7247441
Step 3 — Green cover …
  Green cover: 31.42%
...
── Temporal analysis: Delhi NCR  (2 scenes) ──
  Change 2023-11-15→2024-03-15: loss=12.3%  stable=71.4%  gain=16.3%
```

### 12.5 Checking outputs

After a successful run:

```
output/
├── Delhi_NCR_2023-11-15_ndvi.png
├── Delhi_NCR_2023-11-15_classification.png
├── Delhi_NCR_2023-11-15_stats.png
├── Delhi_NCR_2024-03-15_ndvi.png
├── report_Delhi_NCR/summary.txt
├── analysis_results.json
└── scientific/
    ├── Delhi_NCR_2023-11-15_ndvi_histogram.png
    ├── Delhi_NCR_2023-11-15_band_correlation.png
    ├── Delhi_NCR_2023-11-15_index_comparison.png
    ├── Delhi_NCR_2023-11-15_feature_space.png
    ├── Delhi_NCR_ndvi_timeseries.png
    ├── Delhi_NCR_2023-11-15_to_2024-03-15_change.png
    ├── Delhi_NCR_phenology_heatmap.png
    └── Delhi_NCR_greencover_timeseries.png
```

---

## 13. Module and API Reference

### 13.1 `src/config.py` — Global constants

| Constant | Type | Default | Description |
|---|---|---|---|
| `ROOT_DIR` | `Path` | project root | Resolved absolute path to project root |
| `DATA_DIR` | `Path` | `root/data` | Default data directory |
| `OUTPUT_DIR` | `Path` | `root/output` | Default output directory |
| `DEFAULT_NDVI_THRESHOLD` | `float` | `0.4` | Green cover threshold |
| `VEGETATION_CLASSES` | `dict` | see §7.1 | NDVI class boundaries |
| `DEFAULT_PIXEL_SIZE_M` | `float` | `30.0` | Landsat pixel size |
| `EVI_GAIN` | `float` | `2.5` | EVI G coefficient |
| `EVI_C1` | `float` | `6.0` | EVI C1 coefficient |
| `EVI_C2` | `float` | `7.5` | EVI C2 coefficient |
| `DEFAULT_DPI` | `int` | `300` | Figure save resolution |
| `DEFAULT_FIG_SIZE` | `tuple` | `(12, 10)` | Default figure size in inches |

### 13.2 `src/sensor_config.py` — Sensor profiles

**`SensorProfile`** (frozen dataclass):

| Field | Type | Description |
|---|---|---|
| `name` | `str` | Human-readable sensor name |
| `reflectance_scale` | `float` | $M_\rho$ multiplicative factor |
| `reflectance_offset` | `float` | $A_\rho$ additive offset |
| `nodata_value` | `float \| None` | DN value treated as NoData |
| `valid_min` | `float` | Minimum valid raw DN |
| `valid_max` | `float` | Maximum valid raw DN |
| `default_pixel_size_m` | `float` | Native GSD in metres |
| `supported_extensions` | `tuple[str]` | File extensions (e.g. `(".tif",)`) |

**`get_profile(sensor_key: str) → SensorProfile`**  
Returns the profile for `"landsat8"`, `"landsat9"`, or `"sentinel2"`. Raises `ValueError` for unknown keys.

### 13.3 `src/data_loader.py` — Data loading

**`SatelliteDataLoader`**

| Method | Signature | Description |
|---|---|---|
| `load_scene_from_config` | `(scene_cfg: dict) → dict[str, ndarray]` | Primary production method. Reads one `config.yaml` scene entry |
| `load_landsat_scene` | `(red, nir, blue=None, sensor="landsat8") → dict` | Direct path loading for Landsat |
| `load_sentinel2_scene` | `(red, nir, blue=None) → dict` | Direct path loading for Sentinel-2 |
| `create_synthetic_data` | `(height, width, seed) → dict` | Test data generator (examples.py only) |
| `save_data` | `(output_path, data, metadata=None)` | Save array to .npy or .csv |

**`VegetationDatabase`**

| Method | Description |
|---|---|
| `add_result(location, date, green_cover, statistics, classification)` | Append one result record |
| `save_results()` | Write all records to `analysis_results.json` |
| `load_results() → list[dict]` | Load records from the JSON file |

### 13.4 `src/ndvi_calculator.py` — Index calculation

**`NDVICalculator(red_band, nir_band)`**

| Method | Returns | Description |
|---|---|---|
| `calculate_ndvi()` | `ndarray` | NDVI; NaN for invalid pixels |
| `calculate_evi(blue_band, g, c1, c2)` | `ndarray` | EVI; requires blue |
| `calculate_savi(L=0.5)` | `ndarray` | SAVI with soil factor L |
| `calculate_msavi2()` | `ndarray` | Self-adjusting MSAVI |
| `calculate_ndwi(swir_band)` | `ndarray` | Vegetation water index |
| `calculate_all_indices(blue, swir, savi_L)` | `dict[str, ndarray]` | All available indices |
| `calculate_green_cover(ndvi_threshold)` | `(float, ndarray)` | Percentage and binary mask |
| `get_ndvi_statistics()` | `dict` | Mean, std, min, max, median, p25, p75, valid_pixels |

**`GreenCoverAnalyzer(ndvi)`**

| Method | Returns | Description |
|---|---|---|
| `classify_vegetation()` | `(ndarray, dict)` | Class map and percentages |
| `get_green_area_stats(pixel_size)` | `dict` | Area in km², green %, breakdown |
| `compute_ndvi_change(ndvi_t1, ndvi_t2)` *(static)* | `ndarray` | Pixel-wise ΔNDVI |
| `classify_change(delta, gain_t, loss_t)` *(static)* | `(ndarray, dict)` | Change map and summary |

---

## 14. Where to Change What

This section maps every common modification to the exact file and variable to edit.

### Change the green cover NDVI threshold

**File:** `config.yaml`  
**Key:** `analysis.ndvi_threshold`  
**Effect:** Affects `calculate_green_cover()`, `plot_green_cover_timeseries()`, and `plot_rgb_ndvi_overlay()`.

### Change the vegetation class boundaries

**File:** `src/config.py`  
**Variable:** `VEGETATION_CLASSES`  
**Note:** If you change these boundaries, also update the hardcoded `lo_hi` lists in `scientific_visualization.py` methods `plot_phenology_heatmap()`, `plot_ndvi_timeseries()`, and `plot_green_cover_timeseries()` for consistency.

### Change the SAVI soil factor (L)

**File:** `config.yaml`  
**Key:** `analysis.savi_L`  
**Range:** $0.0$ (no correction) to $1.0$ (maximum correction).

### Change EVI coefficients (G, C1, C2)

**File:** `src/config.py`  
**Variables:** `EVI_GAIN`, `EVI_C1`, `EVI_C2`  
**Note:** The MODIS standard values (2.5, 6.0, 7.5) are appropriate for most sensors and should only be changed if you are working with a non-standard sensor with different atmospheric characteristics.

### Change change-detection thresholds

**File:** `config.yaml`  
**Keys:** `analysis.change_gain_threshold` and `analysis.change_loss_threshold`

### Change output figure resolution (DPI)

**File:** `config.yaml` → `output.dpi`  
or globally in `src/config.py` → `DEFAULT_DPI`

### Change spatial CV window size

**File:** `config.yaml`  
**Key:** `analysis.spatial_cv_window`  
A larger window smooths out noise but reduces spatial detail. Values between 5 and 50 pixels are typical.

### Add a new satellite sensor

**File:** `src/sensor_config.py`  
**Action:** Add a new `SensorProfile` to `SENSOR_PROFILES` (see §5.4).

### Change where output files are saved

**File:** `config.yaml`  
**Key:** `output.directory` and `output.scientific_subdirectory`

### Disable specific chart types

**File:** `config.yaml`  
**Keys:** `output.save_visualizations` and `output.save_scientific_charts`  
For finer control, comment out specific `_add(...)` calls in the `analyse_scene()` function in `main.py`.

### Add a new vegetation index

1. Add the equation as a method to `NDVICalculator` in `src/ndvi_calculator.py`
2. Register it in `calculate_all_indices()` in the same class
3. Add its colour to `_INDEX_COLOURS` in `src/scientific_visualization.py`
4. Add a corresponding `config.yaml` band key if a new band is needed
5. Add `swir`-style loading in `SatelliteDataLoader.load_scene_from_config()`

---

## 15. Extending the Tool

### 15.1 Adding zonal statistics from a shapefile

The `plot_zonal_stats()` method accepts a `zone_mask` array that you must provide. To generate it from a shapefile (e.g. administrative boundaries), you can use `rasterio.features.rasterize`:

```python
import rasterio
import rasterio.features
import geopandas as gpd
import numpy as np

# Load shapefile
gdf = gpd.read_file("boundaries.shp")

# Open a scene band to get the transform and shape
with rasterio.open("data/landsat/..._B4.TIF") as src:
    transform = src.transform
    shape = src.shape

# Rasterize: assign zone index 0, 1, 2, ... to each geometry
zone_mask = np.full(shape, -1, dtype=np.int16)
for i, geom in enumerate(gdf.geometry):
    burned = rasterio.features.rasterize(
        [(geom, i)], out_shape=shape, transform=transform, fill=-1
    )
    zone_mask = np.where(burned >= 0, burned, zone_mask)

zone_names = list(gdf["name"].values)
```

### 15.2 Exporting results to GeoTIFF

To save NDVI or any index array as a georeferenced GeoTIFF (preserving CRS and transform from the input bands):

```python
import rasterio
import numpy as np

with rasterio.open("data/landsat/..._B4.TIF") as src:
    profile = src.profile.copy()

profile.update(dtype="float32", count=1, nodata=np.nan)

with rasterio.open("output/ndvi.tif", "w", **profile) as dst:
    dst.write(ndvi.astype("float32"), 1)
```

### 15.3 Adding a new temporal chart

Add a method to `ScientificVisualizer` in `src/scientific_visualization.py` following the existing pattern:

```python
def plot_my_new_chart(self, records, location, output_filename=None):
    if not self._require_mpl("plot_my_new_chart"):
        return None
    import matplotlib.pyplot as plt
    ...
    return self._save(fig, output_filename or f"{_safe(location)}_my_chart.png")
```

Then call it from `run_temporal_analysis()` in `main.py`.

---

## 16. References

- **Rouse, J.W. et al. (1973).** Monitoring vegetation systems in the Great Plains with ERTS. *Third ERTS Symposium*, NASA SP-351, 309–317. — *Original NDVI paper.*

- **Huete, A.R. (1988).** A soil-adjusted vegetation index (SAVI). *Remote Sensing of Environment*, 25(3), 295–309. — *SAVI formulation.*

- **Huete, A.R. et al. (1997).** A comparison of vegetation indices over a global set of TM images for EOS-MODIS. *Remote Sensing of Environment*, 59(3), 440–451. — *EVI development.*

- **Huete, A. et al. (2002).** Overview of the radiometric and biophysical performance of the MODIS vegetation indices. *Remote Sensing of Environment*, 83(1–2), 195–213. — *EVI standard coefficients.*

- **Qi, J. et al. (1994).** A modified soil adjusted vegetation index. *Remote Sensing of Environment*, 48(2), 119–126. — *MSAVI2 derivation.*

- **Gao, B.-C. (1996).** NDWI — A normalized difference water index for remote sensing of vegetation liquid water from space. *Remote Sensing of Environment*, 58(3), 257–266. — *NDWI for canopy water content.*

- **Singh, A. (1989).** Review article: Digital change detection techniques using remotely sensed data. *International Journal of Remote Sensing*, 10(6), 989–1003. — *NDVI differencing for change detection.*

- **USGS (2023).** *Landsat Collection 2 Level-2 Science Product Guide*. Version 4.0. U.S. Geological Survey. [https://www.usgs.gov/landsat-missions/landsat-collection-2-level-2-science-product-guide](https://www.usgs.gov/landsat-missions/landsat-collection-2-level-2-science-product-guide) — *Source of scaling constants $M_\rho = 2.75 \times 10^{-5}$, $A_\rho = -0.2$.*

- **ESA (2023).** *Sentinel-2 Level-2A Product Specification*. S2-PDGS-TAS-DI-PSD Issue 14.9. European Space Agency. — *Source of Sentinel-2 scaling constant $M_\rho = 1 \times 10^{-4}$.*

- **Scott, D.W. (1992).** *Multivariate Density Estimation: Theory, Practice, and Visualization.* Wiley. — *Scott's bandwidth rule for KDE.*