# Green Cover Calculator - Theory and Equations

## Table of Contents
1. [Remote Sensing Fundamentals](#remote-sensing-fundamentals)
2. [Vegetation Indices](#vegetation-indices)
3. [Mathematical Formulations](#mathematical-formulations)
4. [Spectral Properties of Vegetation](#spectral-properties-of-vegetation)
5. [Data Processing Pipeline](#data-processing-pipeline)
6. [Classification Methodology](#classification-methodology)
7. [Accuracy Assessment](#accuracy-assessment)
8. [References](#references)

---

## Remote Sensing Fundamentals

### What is Remote Sensing?

Remote sensing is the science of obtaining information about objects or areas from a distance, typically from aircraft or satellites. It relies on measuring electromagnetic radiation (light) reflected or emitted by Earth's surface.

### Electromagnetic Spectrum

The electromagnetic spectrum is divided into different wavelength regions:

| Region | Wavelength | Application |
|--------|-----------|-------------|
| Visible | 400-700 nm | Human vision |
| Near-Infrared (NIR) | 700-1100 nm | Vegetation analysis |
| Short-Wave Infrared (SWIR) | 1100-3000 nm | Moisture content |
| Thermal | 3000-1000000 nm | Temperature measurement |

### Spectral Reflectance Curves

Different surface materials have characteristic spectral reflectance patterns:

```
Reflectance (%)
     ^
100  |              /─────────────
     |             /
 80  |            /        Vegetation (NIR peak)
     |           /
 60  |          /
     |         /
 40  |        /
     |       /
 20  |    ╱\
     |   ╱  \╲
  0  |  ╱____╲╲________
     |  Blue  Red SWIR
     +───────────────────→ Wavelength
     400    700   2500 nm
```

**Key Observation**: Vegetation has low reflectance in the red wavelength (due to chlorophyll absorption) and high reflectance in the near-infrared wavelength (due to leaf cell structure).

---

## Vegetation Indices

Vegetation indices combine reflectance values from different spectral bands to quantify vegetation characteristics. They exploit the spectral differences between vegetation and other surface types.

### Why Vegetation Indices?

1. **Normalization**: Reduce the effect of atmospheric conditions and sun angle variations
2. **Standardization**: Enable comparison across different sensors and time periods
3. **Discrimination**: Distinguish vegetation from water, soil, and other surfaces
4. **Quantification**: Provide numerical measures of vegetation characteristics

---

## Mathematical Formulations

### 1. NDVI (Normalized Difference Vegetation Index)

**Formula:**

$$\text{NDVI} = \frac{\text{NIR} - \text{RED}}{\text{NIR} + \text{RED}}$$

Where:
- **NIR** = Reflectance in the near-infrared band (typically Landsat Band 5)
- **RED** = Reflectance in the red band (typically Landsat Band 4)

**Range:** -1.0 to +1.0

**Derivation:**
The NDVI is derived from the simple ratio (NIR/RED) through normalization:

$$\text{Simple Ratio} = \frac{\text{NIR}}{\text{RED}}$$

$$\text{NDVI} = \frac{\text{Simple Ratio} - 1}{\text{Simple Ratio} + 1}$$

**Advantages:**
- Simple and computationally efficient
- Normalized scale reduces atmospheric effects
- Widely available from multiple sensors
- Long historical data record

**Limitations:**
- Saturates at high vegetation densities
- Sensitive to atmospheric aerosols
- Affected by soil background
- Can produce false signals in mountainous terrain

### 2. EVI (Enhanced Vegetation Index)

**Formula:**

$$\text{EVI} = G \times \frac{\text{NIR} - \text{RED}}{\text{NIR} + C_1 \times \text{RED} - C_2 \times \text{BLUE} + L}$$

Where:
- **NIR** = Near-infrared reflectance
- **RED** = Red reflectance
- **BLUE** = Blue reflectance (typically Band 2)
- **G** = Gain factor (typically 2.5)
- **C₁** = Red coefficient (typically 6.0)
- **C₂** = Blue coefficient (typically 7.5)
- **L** = Soil adjustment factor (typically 1.0)

**Range:** -1.0 to +1.0

**Improvements over NDVI:**
- Better sensing of vegetation in areas with moderate to high biomass
- Decouples vegetation signal from soil background through blue band
- Reduces atmospheric influences through optimized coefficients
- More sensitive to changes in leaf area index (LAI)

**Standard Parameters (MODIS calibration):**
```
G = 2.5    (Gain factor for amplitude optimization)
C₁ = 6.0   (Aerosol resistance coefficient)
C₂ = 7.5   (Atmospheric resistance coefficient)
L = 1.0    (Soil line intercept)
```

### 3. SAVI (Soil-Adjusted Vegetation Index)

**Formula:**

$$\text{SAVI} = (1 + L) \times \frac{\text{NIR} - \text{RED}}{\text{NIR} + \text{RED} + L}$$

Where:
- **L** = Soil adjustment factor (typically 0.5)

**Range:** -1.0 to +1.0

**Purpose:** Minimizes the effect of soil background reflectance on NDVI

**Special Values of L:**
- L = 0: Equivalent to NDVI
- L = 0.5: Used for moderate vegetation coverage
- L = 1.0: Used for sparse vegetation

### 4. OSAVI (Optimized SAVI)

**Formula:**

$$\text{OSAVI} = (1 + 0.16) \times \frac{\text{NIR} - \text{RED}}{\text{NIR} + \text{RED} + 0.16}$$

A refined version of SAVI with an optimized L value of 0.16

### 5. MSAVI (Modified SAVI)

**Formula:**

$$\text{MSAVI} = \frac{2 \times \text{NIR} + 1 - \sqrt{(2 \times \text{NIR} + 1)^2 - 8 \times (\text{NIR} - \text{RED})}}{2}$$

**Purpose:** Automatic soil adjustment that doesn't require user-defined parameter

### 6. CI (Chlorophyll Index)

**Formula:**

$$\text{CI} = \frac{\text{NIR}}{\text{GREEN}} - 1$$

Where:
- **GREEN** = Green band reflectance

**Application:** Direct estimation of chlorophyll content

### 7. GNDVI (Green NDVI)

**Formula:**

$$\text{GNDVI} = \frac{\text{NIR} - \text{GREEN}}{\text{NIR} + \text{GREEN}}$$

**Advantage:** More sensitive to chlorophyll variations than traditional NDVI

---

## Spectral Properties of Vegetation

### Chlorophyll Absorption

Chlorophyll absorbs light primarily in two wavelength regions:

**Chlorophyll-a absorption maxima:**
- **Blue band:** ~430 nm (strong absorption)
- **Red band:** ~662 nm (strong absorption)

**Formula for chlorophyll density estimate:**
$$\text{Chlorophyll} \propto \text{NIR/Red Ratio}$$

### Leaf Architecture Effect

The high NIR reflectance of vegetation is due to:

1. **Cell wall structure** of mesophyll cells
2. **Air-filled intercellular spaces** scatter NIR radiation
3. **Minimal NIR absorption** by plant biochemistry

**Reflectance contributions:**
- Direct reflection: ~5%
- Scattered reflection: ~50%
- Total NIR reflectance: 40-60% (healthy vegetation)

---

## Data Processing Pipeline

### Step 1: Data Acquisition

Remote sensing data acquisition workflow:

```
Satellite/Aircraft
       ↓
Multispectral Sensor
       ↓
Raw Digital Numbers (DNs)
       ↓
Radiometric Calibration
       ↓
At-Sensor Radiance (L)
       ↓
Atmospheric Correction
       ↓
Top-of-Atmosphere (TOA) Reflectance
       ↓
Surface Reflectance
       ↓
Use for NDVI/EVI Calculation
```

### Step 2: Radiometric Calibration

Convert Digital Numbers to radiance:

$$L = ML \times Q_{\text{cal}} + AL$$

Where:
- **L** = Spectral radiance (W/(m² × sr × μm))
- **ML** = Radiance multiplicative scaling factor
- **Q_cal** = Quantized and calibrated standard product pixel values (DN)
- **AL** = Radiance additive scaling factor

### Step 3: Atmospheric Correction

Convert at-sensor radiance to surface reflectance:

$$\rho = \frac{\pi \times L_{\lambda} \times d^2}{E_{\text{sun}} \times \cos(\theta)}$$

Where:
- **ρ** = Surface reflectance (unitless)
- **L_λ** = Spectral radiance (W/(m² × sr × μm))
- **d** = Earth-Sun distance in Astronomical Units (AU)
- **E_sun** = Exoatmospheric solar spectral irradiance
- **θ** = Sun zenith angle

### Step 4: Index Calculation

$$\text{VI} = f(\rho_{\text{NIR}}, \rho_{\text{RED}}, ...)$$

Apply appropriate vegetation index formula

### Step 5: Classification

Apply thresholds to classify pixels into categories

---

## Classification Methodology

### NDVI Classification Scheme

The green cover calculation uses the following vegetation classification:

| Class | NDVI Range | Description | Color | Characteristics |
|-------|-----------|-------------|-------|-----------------|
| Water | < 0.0 | Open water bodies | Blue | Negative NDVI due to water absorption |
| Bare Soil | 0.0 - 0.2 | Exposed soil, rock | Brown | Minimal vegetation cover |
| Sparse Vegetation | 0.2 - 0.4 | Grassland, shrubs | Yellow | <50% vegetation cover |
| Moderate Vegetation | 0.4 - 0.6 | Crop fields, forest edges | Orange | 50-80% vegetation cover |
| Dense Vegetation | 0.6 - 1.0 | Dense forest, dense crops | Green | >80% vegetation cover |

### Threshold Selection

**Default threshold for green cover: NDVI ≥ 0.4**

Rationale:
- Below 0.4: Sparse or minimal vegetation
- Above 0.4: Moderate to dense vegetation with continuous cover

**Customizable thresholds:**
```
Green Cover percentage = (Pixels with NDVI ≥ threshold) / Total valid pixels × 100
```

---

## Area Calculations

### Pixel Area Calculation

For satellite imagery with known pixel size:

$$\text{Area}_{[\text{pixel}]} = \text{Pixel Size}^2$$

**Common pixel sizes:**
- Landsat 8/9: 30 m
- Sentinel-2: 10 m or 20 m
- MODIS: 250 m, 500 m, or 1000 m

### Green Cover Area Calculation

$$\text{Green Area}_{[\text{km}^2]} = \text{Number of Green Pixels} \times \frac{(\text{Pixel Size}_{[\text{m}]})^2}{10^6}$$

### Green Cover Percentage

$$\text{Green Cover}_{[\%]} = \frac{\text{Number of Green Pixels}}{\text{Total Valid Pixels}} \times 100$$

### Vegetation Type Area Distribution

$$\text{Area}_{[\text{km}^2]} = \frac{\text{Pixels in Class}}{\text{Total Pixels}} \times \text{Total Area}_{[\text{km}^2]}$$

---

## Accuracy Assessment

### Confusion Matrix

Evaluation of classification accuracy:

```
                 Classified
                  Yes    No
Actual   Yes   [TP]    [FN]
         No    [FP]    [TN]
```

Where:
- **TP** = True Positives (vegetation correctly classified)
- **FP** = False Positives (non-vegetation classified as vegetation)
- **FN** = False Negatives (vegetation missed)
- **TN** = True Negatives (non-vegetation correctly classified)

### Accuracy Metrics

**Overall Accuracy:**
$$\text{OA} = \frac{\text{TP} + \text{TN}}{\text{TP} + \text{TN} + \text{FP} + \text{FN}} \times 100\%$$

**Producer's Accuracy (Sensitivity):**
$$\text{PA} = \frac{\text{TP}}{\text{TP} + \text{FN}} \times 100\%$$

**User's Accuracy (Precision):**
$$\text{UA} = \frac{\text{TP}}{\text{TP} + \text{FP}} \times 100\%$$

**Kappa Coefficient:**
$$\kappa = \frac{\text{OA} - E_c}{1 - E_c}$$

Where $E_c$ is the expected accuracy by chance

---

## Satellite Specifications

### Landsat 8/9

**Multispectral Bands:**

| Band | Name | Wavelength (μm) | Resolution |
|------|------|-----------------|-----------|
| 1 | Coastal/Aerosol | 0.43 - 0.45 | 30 m |
| 2 | Blue | 0.45 - 0.51 | 30 m |
| 3 | Green | 0.53 - 0.59 | 30 m |
| **4** | **Red** | **0.64 - 0.67** | **30 m** |
| **5** | **NIR** | **0.85 - 0.88** | **30 m** |
| 6 | SWIR 1 | 1.57 - 1.65 | 30 m |
| 7 | SWIR 2 | 2.11 - 2.29 | 30 m |
| 8 | Panchromatic | 0.50 - 0.68 | 15 m |
| 9 | Cirrus | 1.36 - 1.38 | 30 m |

**NDVI bands:** Red (Band 4) and NIR (Band 5)

### Sentinel-2

**Multispectral Bands:**

| Band | Name | Wavelength (μm) | Resolution |
|------|------|-----------------|-----------|
| 1 | Coastal aerosol | 0.433 - 0.453 | 60 m |
| 2 | Blue | 0.457 - 0.523 | 10 m |
| 3 | Green | 0.542 - 0.578 | 10 m |
| **4** | **Red** | **0.650 - 0.680** | **10 m** |
| **8** | **NIR** | **0.785 - 0.900** | **10 m** |
| 9 | Water vapor | 0.935 - 0.955 | 60 m |
| 10 | SWIR cirrus | 1.360 - 1.390 | 60 m |
| 11 | SWIR 1 | 1.565 - 1.655 | 20 m |
| 12 | SWIR 2 | 2.100 - 2.280 | 20 m |

**NDVI bands:** Red (Band 4) and NIR (Band 8)

---

## Sensor Comparison

### NDVI Calculation Differences

Different satellite sensors may produce slightly different NDVI values due to:

1. **Spectral band characteristics** - Different central wavelengths
2. **Atmospheric correction** - Different algorithms
3. **Calibration differences** - Radiometric differences
4. **Spatial resolution** - Landsat (30m) vs Sentinel-2 (10m)

**Typical NDVI correlations:**
- Landsat 8 vs Sentinel-2: R² ≈ 0.95
- Difference: ±0.03 (acceptable for most applications)

---

## Quality Assurance

### Sources of Uncertainty

1. **Atmospheric conditions:**
   - Cloud cover (creates invalid pixels)
   - Aerosol opacity
   - Water vapor variations

2. **Radiometric errors:**
   - Sensor noise
   - Radiometric calibration uncertainty (±2-3%)
   - Gain/offset errors

3. **Geometric errors:**
   - Registration errors (sub-pixel acceptable)
   - Projection differences

4. **Algorithmic limitations:**
   - NDVI saturation at high LAI (>3-4)
   - Soil background effects
   - Atmospheric coupling

### Quality Flags

Pixels should be flagged as invalid if:
```
1. Cloud detected
2. Cloud shadow present
3. Sensor malfunction
4. Saturation in any band
5. Extreme viewing angle (>60°)
6. NIR + Red = 0 (division error)
```

---

## Advanced Topics

### Time Series Analysis

**Vegetation phenology:**

$$\text{NDVI}(t) = \text{baseline} + A \times \sin\left(\frac{2\pi(t - t_0)}{T}\right)$$

Where:
- **t** = Time (in days)
- **A** = Amplitude (related to vegetation vigor)
- **T** = Period (seasonal cycle ≈ 365 days)
- **t₀** = Phase (start of growing season)

### Leaf Area Index (LAI) Retrieval

Regression model for LAI estimation:

$$\text{LAI} = \alpha \times \ln\left(\frac{1 + \text{NDVI}}{1 - \text{NDVI}}\right) + \beta$$

Typical coefficients: α ≈ 2.0, β ≈ -0.5

### Biomass Estimation

Empirical relationship between NDVI and above-ground biomass:

$$\text{AGB} = a \times \text{NDVI}^b + c$$

Where a, b, c are site-specific calibration parameters

---

## Implementation Notes

### Handling Division by Zero

In NDVI calculation, when NIR + RED = 0:

```
if (NIR + RED) == 0:
    NDVI = NaN    (Not a Number)
else:
    NDVI = (NIR - RED) / (NIR + RED)
```

### Data Type Considerations

**Input data (reflectance):**
- Range: 0 to 1.0 (if normalized) or 0 to 255/10000 (if scaled integers)
- Must convert to floating point before calculation

**Output NDVI:**
- Range: -1.0 to +1.0
- Store as 32-bit float or scaled integer (multiply by 10000, store as int16)

### Handling Missing Data

```
1. Identify invalid pixels (clouds, shadows)
2. Create validity mask
3. Exclude invalid pixels from statistics
4. Report percentage of valid data
```

---

## References

### Primary Literature

1. Tucker, C. J. (1979). "Red and Photographic Infrared Linear Combinations for Monitoring Vegetation." *Remote Sensing of Environment*, 8(2), 127-150.

2. Rouse Jr, J. W., Haas, R. H., Schell, J. A., & Deering, D. W. (1973). "Monitoring vegetation systems in the Great Plains with ERTS." *NASA Goddard Space Flight Center, Greenbelt, MD*, 309, 40.

3. Huete, A., Didan, K., Miura, T., Rodriguez, E. P., Gao, X., & Ferreira, L. G. (2002). "Overview of the Radiometric and Biophysical Performance of the MODIS Vegetation Indices." *Remote Sensing of Environment*, 83(1), 195-213.

4. Bannari, A., Morin, D., Bonn, F., & Huete, A. R. (1995). "A review of vegetation indices." *Remote Sensing Reviews*, 13(1-2), 95-120.

### Satellite Documentation

5. USGS Landsat 8 Data Users Handbook (https://www.usgs.gov/media/files/landsat-8-data-users-handbook)

6. ESA Sentinel-2 User Handbook (https://sentinel.esa.int/documents/247904/685211/Sentinel-2_User_Handbook)

### Atmospheric Correction

7. Vermote, E. F., Tanré, D., Deuzé, J. L., Herman, M., & Morcrette, J. J. (1997). "Second simulation of the satellite signal in the solar spectrum, 6S: An overview." *IEEE Transactions on Geoscience and Remote Sensing*, 35(3), 675-686.

---

## Appendix: Quick Reference

### Common NDVI Thresholds

```
NDVI < 0.0      → No vegetation
NDVI 0.0-0.2    → Sparse vegetation
NDVI 0.2-0.4    → Low vegetation
NDVI 0.4-0.6    → Moderate vegetation
NDVI 0.6-0.8    → High vegetation
NDVI > 0.8      → Very dense vegetation
```

### Recommended Reading Order

1. Start with **Remote Sensing Fundamentals**
2. Review **Spectral Properties of Vegetation**
3. Study **Mathematical Formulations** (focus on NDVI and EVI)
4. Understand **Data Processing Pipeline**
5. Apply **Classification Methodology**
6. Reference **Satellite Specifications** as needed

### Quick Calculation Checklist

- [ ] Load red and NIR bands
- [ ] Convert to floating point
- [ ] Handle invalid pixels (NaN, 0/0)
- [ ] Calculate NDVI = (NIR - RED) / (NIR + RED)
- [ ] Apply classification thresholds
- [ ] Calculate green cover percentage
- [ ] Calculate areas (× pixel size²)
- [ ] Validate results against ground truth
- [ ] Generate visualizations

---

**Last Updated:** February 2024  
**Version:** 1.0.0  
**Maintained By:** Remote Sensing Team
