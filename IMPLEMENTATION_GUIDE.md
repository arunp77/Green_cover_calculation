# Implementation Guide - Green Cover Calculator

## Table of Contents
1. [Quick Start](#quick-start)
2. [API Reference](#api-reference)
3. [Usage Examples](#usage-examples)
4. [Data Format Guide](#data-format-guide)
5. [Performance Optimization](#performance-optimization)
6. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Installation

```bash
# Clone repository
git clone <repository-url>
cd test_folder

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Minimal Example

```python
from src.ndvi_calculator import NDVICalculator
import numpy as np

# Create sample data
red_band = np.random.rand(100, 100) * 255
nir_band = np.random.rand(100, 100) * 255

# Calculate NDVI
calc = NDVICalculator(red_band, nir_band)
ndvi = calc.calculate_ndvi()

# Get green cover
green_cover, mask = calc.calculate_green_cover(ndvi_threshold=0.4)
print(f"Green cover: {green_cover:.2f}%")
```

---

## API Reference

### NDVICalculator

```python
class NDVICalculator(red_band, nir_band)
```

#### Methods

**`calculate_ndvi()`**
```python
ndvi = calc.calculate_ndvi()
```
- **Returns:** `numpy.ndarray` - NDVI values (-1 to 1)
- **Side effects:** Sets `self.ndvi` and `self.valid_mask`

**`calculate_green_cover(ndvi_threshold=0.4)`**
```python
green_percent, binary_mask = calc.calculate_green_cover(ndvi_threshold=0.4)
```
- **Parameters:** 
  - `ndvi_threshold` (float): NDVI threshold for green classification
- **Returns:** 
  - Tuple of (green_cover_percentage, binary_mask)
- **Example:**
  ```python
  gc, mask = calc.calculate_green_cover(ndvi_threshold=0.3)  # 30% coverage threshold
  ```

**`calculate_evi(blue_band, g=2.5, c1=6.0, c2=7.5)`**
```python
evi = calc.calculate_evi(blue_band, g=2.5, c1=6.0, c2=7.5)
```
- **Parameters:**
  - `blue_band` (numpy.ndarray): Blue band reflectance
  - `g` (float): Gain factor (default: 2.5)
  - `c1` (float): Red coefficient (default: 6.0)
  - `c2` (float): Blue coefficient (default: 7.5)
- **Returns:** `numpy.ndarray` - EVI values (-1 to 1)
- **Formula:** 
  ```
  EVI = g * (NIR - RED) / (NIR + c1*RED - c2*BLUE + 1)
  ```

**`get_ndvi_statistics()`**
```python
stats = calc.get_ndvi_statistics()
```
- **Returns:** Dictionary with keys:
  - `mean` (float): Mean NDVI value
  - `std` (float): Standard deviation
  - `min` (float): Minimum value
  - `max` (float): Maximum value
  - `median` (float): Median value
  - `valid_pixels` (int): Number of valid pixels

---

### GreenCoverAnalyzer

```python
class GreenCoverAnalyzer(ndvi)
```

#### Methods

**`classify_vegetation()`**
```python
classification_map, percentages = analyzer.classify_vegetation()
```
- **Returns:** 
  - `classification_map` (numpy.ndarray): Integer array (0-4)
  - `percentages` (dict): Class percentages

**Classification classes:**
```python
{
    0: 'water',               # NDVI < 0.0
    1: 'bare_soil',          # 0.0 ≤ NDVI < 0.2
    2: 'sparse_vegetation',  # 0.2 ≤ NDVI < 0.4
    3: 'moderate_vegetation',# 0.4 ≤ NDVI < 0.6
    4: 'dense_vegetation'    # 0.6 ≤ NDVI ≤ 1.0
}
```

**`get_green_area_stats(pixel_size=30.0)`**
```python
area_stats = analyzer.get_green_area_stats(pixel_size=30.0)
```
- **Parameters:**
  - `pixel_size` (float): Pixel size in meters (default: 30m for Landsat)
- **Returns:** Dictionary with keys:
  - `total_area_km2` (float): Total study area
  - `green_area_km2` (float): Vegetated area
  - `green_cover_percentage` (float): % of green coverage
  - `vegetation_breakdown` (dict): Breakdown by class
  - `pixel_size_m` (float): Input pixel size

### SatelliteDataLoader

```python
class SatelliteDataLoader(data_directory="data")
```

#### Methods

**`create_synthetic_data(height=100, width=100, seed=42)`**
```python
bands = loader.create_synthetic_data(height=150, width=150, seed=42)
```
- **Returns:** Dictionary with keys: `'red'`, `'nir'`, `'blue'`
- **Use:** For testing without real satellite data

**`load_geotiff(filepath)`**
```python
data = loader.load_geotiff("path/to/band.tif")
```
- **Returns:** `numpy.ndarray` - Band data
- **Requires:** rasterio library

**`load_landsat_scene(red_path, nir_path, blue_path=None)`**
```python
bands = loader.load_landsat_scene(
    red_band_path="B4.TIF",
    nir_band_path="B5.TIF",
    blue_band_path="B2.TIF"
)
```
- **Returns:** Dictionary with loaded bands

### VegetationVisualizer

```python
class VegetationVisualizer(output_directory="output")
```

#### Methods

**`plot_ndvi(ndvi, title, output_filename, cmap)`**
```python
path = visualizer.plot_ndvi(ndvi, 
                            title="NDVI Map",
                            output_filename="ndvi.png",
                            cmap="RdYlGn")
```
- **Returns:** Path to saved image or None

**`plot_vegetation_classification(classification, title, output_filename)`**
```python
path = visualizer.plot_vegetation_classification(
    classification_map,
    output_filename="classification.png"
)
```

**`plot_rgb_composite(red, green, blue, title, output_filename)`**
```python
path = visualizer.plot_rgb_composite(red_band, green_band, blue_band)
```

**`plot_statistics_summary(stats, title, output_filename)`**
```python
path = visualizer.plot_statistics_summary(
    ndvi_stats,
    output_filename="stats.png"
)
```

---

## Usage Examples

### Example 1: Basic Analysis

```python
from src.ndvi_calculator import NDVICalculator
from src.data_loader import SatelliteDataLoader
from src.visualization import VegetationVisualizer
import numpy as np

# 1. Load data
loader = SatelliteDataLoader()
bands = loader.create_synthetic_data(height=200, width=200)

# 2. Calculate NDVI
calc = NDVICalculator(bands['red'], bands['nir'])
ndvi = calc.calculate_ndvi()

# 3. Calculate green cover
green_cover, green_mask = calc.calculate_green_cover(ndvi_threshold=0.4)

# 4. Get statistics
stats = calc.get_ndvi_statistics()

# 5. Visualize
visualizer = VegetationVisualizer()
visualizer.plot_ndvi(ndvi, title="My Study Area")

print(f"Green cover: {green_cover:.2f}%")
print(f"NDVI mean: {stats['mean']:.4f}")
```

### Example 2: Multi-Index Comparison

```python
# Calculate multiple indices
ndvi = calc.calculate_ndvi()
evi = calc.calculate_evi(bands['blue'])

# Get statistics for both
ndvi_stats = calc.get_ndvi_statistics()

# Visualize comparison
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
axes[0].imshow(ndvi, cmap='RdYlGn', vmin=-1, vmax=1)
axes[0].set_title(f'NDVI (mean={ndvi_stats["mean"]:.3f})')
axes[1].imshow(evi, cmap='viridis', vmin=-1, vmax=1)
axes[1].set_title('EVI')
plt.show()
```

### Example 3: Time Series Analysis

```python
from datetime import datetime, timedelta

# Multiple dates
results = []
base_date = datetime(2024, 1, 1)

for i in range(12):  # 12 months
    # Load data for each month
    monthly_data = load_monthly_data(base_date + timedelta(days=30*i))
    
    # Calculate NDVI
    calc = NDVICalculator(monthly_data['red'], monthly_data['nir'])
    ndvi = calc.calculate_ndvi()
    green_cover, _ = calc.calculate_green_cover()
    
    results.append({
        'date': base_date + timedelta(days=30*i),
        'green_cover': green_cover
    })

# Plot time series
dates = [r['date'] for r in results]
gc_values = [r['green_cover'] for r in results]
plt.plot(dates, gc_values, marker='o')
plt.ylabel('Green Cover (%)')
plt.xlabel('Date')
plt.show()
```

### Example 4: Area of Interest (AOI) Analysis

```python
# Load full scene
loader = SatelliteDataLoader()
full_red = loader.load_geotiff("full_scene_red.tif")
full_nir = loader.load_geotiff("full_scene_nir.tif")

# Extract AOI (e.g., rows 100-300, cols 200-400)
aoi_row_start, aoi_row_end = 100, 300
aoi_col_start, aoi_col_end = 200, 400

red_aoi = full_red[aoi_row_start:aoi_row_end, aoi_col_start:aoi_col_end]
nir_aoi = full_nir[aoi_row_start:aoi_row_end, aoi_col_start:aoi_col_end]

# Analyze AOI
calc = NDVICalculator(red_aoi, nir_aoi)
ndvi = calc.calculate_ndvi()
green_cover, _ = calc.calculate_green_cover()
```

---

## Data Format Guide

### Input Data Requirements

#### Minimum Required Bands
- **Red band** (e.g., Landsat Band 4): 400-700 nm
- **NIR band** (e.g., Landsat Band 5): 700-1100 nm

#### Optional Bands
- **Blue band** (e.g., Landsat Band 2): For EVI calculation

### Data Types and Ranges

| Aspect | Requirement | Notes |
|--------|------------|-------|
| Data Type | uint8, uint16, or float32 | Will be converted to float |
| Value Range | 0-255 (uint8) or 0-10000 (scaled) | Any positive range acceptable |
| Dimensions | 2D arrays or GeoTIFF | (rows, columns) |
| Missing Data | NaN or 0 | Will be flagged as invalid |

### Coordinate Systems

**Supported formats:**
- UTM (Projected)
- Geographic (Lat/Lon)
- Any EPSG-defined projection (with rasterio)

**Note:** Coordinates handled automatically by rasterio for GeoTIFF

### File Formats

**Supported Input:**
```
.tif, .tiff    - GeoTIFF (requires rasterio)
.npy           - NumPy arrays
.txt, .csv     - Plain text/CSV
```

**Output Formats:**
```
.png           - Visualizations
.json          - Analysis results
.npy           - Processed arrays
.txt           - Reports
```

---

## Performance Optimization

### Memory Usage

**For large images:**

```python
# Process in tiles instead of full image
tile_size = 512
n_tiles_y = ndvi.shape[0] // tile_size
n_tiles_x = ndvi.shape[1] // tile_size

results = []
for i in range(n_tiles_y):
    for j in range(n_tiles_x):
        y_start, y_end = i * tile_size, (i+1) * tile_size
        x_start, x_end = j * tile_size, (j+1) * tile_size
        
        tile_ndvi = ndvi[y_start:y_end, x_start:x_end]
        tile_gc, _ = analyze_tile(tile_ndvi)
        results.append(tile_gc)
```

### Computation Speed

**Benchmark (150x150 image):**
```
NDVI calculation:      ~0.5 ms
Green cover calc:      ~0.3 ms
Classification:        ~0.4 ms
EVI calculation:       ~0.6 ms
Visualization:         ~50-100 ms
Total:                 ~52-102 ms
```

**Optimization tips:**
1. Use NumPy's vectorized operations
2. Avoid Python loops; use array operations
3. Cache results for repeated analysis
4. Use non-interactive matplotlib backend

---

## Troubleshooting

### Issue: "Division by Zero" Warning

**Cause:** Some pixels have NIR + RED = 0

**Solution:**
```python
# This is handled automatically, but check:
valid_mask = calc.valid_mask
print(f"Invalid pixels: {np.sum(~valid_mask)} / {ndvi.size}")

# Visualize invalid pixels
plt.imshow(~valid_mask)
plt.title("Invalid Pixels (black)")
plt.show()
```

### Issue: NDVI Values Outside [-1, 1] Range

**Cause:** Data not properly normalized or in wrong units

**Solution:**
```python
# Check data range
print(f"Red range: {red.min()}-{red.max()}")
print(f"NIR range: {nir.min()}-{nir.max()}")

# If needed, normalize to 0-1
red_norm = (red - red.min()) / (red.max() - red.min())
nir_norm = (nir - nir.min()) / (nir.max() - nir.min())
```

### Issue: All Green Cover = 0%

**Cause:** Threshold too high or data only shows water/bare soil

**Solutions:**
```python
# 1. Lower threshold
green_cover, _ = calc.calculate_green_cover(ndvi_threshold=0.2)

# 2. Check NDVI values
print(f"NDVI range: {np.nanmin(ndvi)}-{np.nanmax(ndvi)}")
plt.hist(ndvi.flatten(), bins=50)
plt.show()

# 3. Visualize raw NDVI
visualizer.plot_ndvi(ndvi)
```

### Issue: "No module named 'rasterio'"

**Solution:**
```bash
pip install rasterio
# or use alternative:
from PIL import Image
data = np.array(Image.open("file.tif"))
```

### Issue: Memory Error with Large Files

**Solution - Process by tiles:**
```python
# Load only required portion
with rasterio.open("large_file.tif") as src:
    window = rasterio.windows.Window(100, 100, 500, 500)
    data = src.read(1, window=window)
```

### Issue: Matplotlib Not Showing Plots

**Solution:**
```python
# Use non-interactive backend (default in this project)
import matplotlib
matplotlib.use('Agg')  # or 'TkAgg' for GUI

# Save instead of show
plt.savefig('output.png', dpi=300)
```

### Issue: Results Don't Match Expected Values

**Debugging checklist:**
```python
# 1. Verify data
print(f"Red: min={red.min()}, max={red.max()}, dtype={red.dtype}")
print(f"NIR: min={nir.min()}, max={nir.max()}, dtype={nir.dtype}")

# 2. Check calculation
sample_red, sample_nir = 100, 150
expected_ndvi = (sample_nir - sample_red) / (sample_nir + sample_red)
print(f"Expected NDVI at (0,0): {expected_ndvi:.4f}")
print(f"Actual NDVI at (0,0): {ndvi[0,0]:.4f}")

# 3. Validate thresholds
stats = calc.get_ndvi_statistics()
print(f"NDVI stats: {stats}")

# 4. Check classification
classification, percentages = analyzer.classify_vegetation()
print(f"Classification percentages: {percentages}")
```

---

## FAQ

**Q: Which index should I use - NDVI or EVI?**

A: Use NDVI for quick analysis and comparisons. Use EVI for areas with:
- High vegetation density (forests)
- Atmospheric sensitivity concerns
- Need for atmospheric compensation

**Q: What pixel size should I use?**

A: Use the actual sensor resolution:
- Landsat: 30 m
- Sentinel-2: 10-20 m  
- MODIS: 250-1000 m

**Q: How do I get satellite data?**

A:
- **Landsat:** USGS Earth Explorer (https://earthexplorer.usgs.gov/)
- **Sentinel-2:** Copernicus (https://scihub.copernicus.eu/)
- **MODIS:** NASA LP DAAC (https://lpdaac.usgs.gov/)

**Q: Can I use this for real-time monitoring?**

A: Yes, with data latency:
- Landsat 8/9: 1-3 days
- Sentinel-2: <1 day
- MODIS: within 4 hours

**Q: How accurate is the green cover calculation?**

A: Typical accuracy: 85-95% depending on:
- Ground truth availability
- Cloud cover
- Atmospheric conditions
- NDVI threshold selection

---

**Document Version:** 1.0.0  
**Last Updated:** February 2024
