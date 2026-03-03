# Satellite Data Acquisition Guide

## Table of Contents
1. [Landsat Data](#landsat-data)
2. [Sentinel-2 Data](#sentinel-2-data)
3. [MODIS Data](#modis-data)
4. [Comparison of Data Sources](#comparison-of-data-sources)
5. [How to Search and Download](#how-to-search-and-download)
6. [Data Preprocessing](#data-preprocessing)
7. [Working with Downloaded Data](#working-with-downloaded-data)
8. [Tips and Best Practices](#tips-and-best-practices)

---

## Landsat Data

### Overview

**Landsat 8/9** satellites provide free, publicly available imagery of Earth's surface.

**Key Characteristics:**
- Resolution: 30 meters (multispectral), 15 meters (panchromatic)
- Temporal coverage: Every 16 days
- Free and open-source
- Radiometrically calibrated
- Extensive historical archive (since 1972)

### Where to Get Landsat Data

#### 1. **USGS Earth Explorer** (RECOMMENDED for beginners)

📍 **Website:** https://earthexplorer.usgs.gov/

**Step-by-Step Guide:**

1. **Visit the website** and create a free account (if needed)
   
2. **Define your study area:**
   - Click "Enter Coordinates" in the left panel
   - Select your area of interest using:
     - Address search
     - Latitude/Longitude coordinates
     - Draw on map
     - Upload shapefile

3. **Select date range:**
   - Choose start and end dates
   - Recommendation: 1-3 months for minimal cloud cover

4. **Filter by data collection:**
   - Under "Data Sets" tab, expand "Landsat"
   - Select "Landsat Collection 2 Level-2" (atmospheric corrected)
   - Select "Landsat 8/9"

5. **Apply filters:**
   - Click "Additional Criteria"
   - Set cloud cover: **0-20%** (or your preference)
   - Apply filters

6. **Browse results:**
   - Results show available scenes
   - Thumbnails show cloud cover percentage
   - Check quick preview by clicking thumbnail

7. **Download data:**
   - Click "Download Options" for desired scene
   - Select "Product Bundle" (includes all bands)
   - Download will start (3-5 GB per scene)

**Bands included:**
```
Band 2  - Blue (0.45-0.51 μm)
Band 3  - Green (0.53-0.59 μm)
Band 4  - Red (0.64-0.67 μm)      ← For NDVI
Band 5  - NIR (0.85-0.88 μm)      ← For NDVI
Band 6  - SWIR 1 (1.57-1.65 μm)
Band 7  - SWIR 2 (2.11-2.29 μm)
```

#### 2. **USGS GloVis** (Quick preview)

📍 **Website:** https://glovis.usgs.gov/

**Advantages:**
- Simpler interface
- Good for quick browsing
- Preview images

**Disadvantages:**
- Limited filtering options
- Slower for large area searches

#### 3. **Google Cloud Storage**

📍 **Website:** https://cloud.google.com/storage/docs/public-datasets/landsat

**Features:**
- Entire Landsat archive on Google Cloud
- Very fast downloads if using Google Cloud services
- Requires Google Cloud account (free tier available)

**Command-line download:**
```bash
gsutil -m cp gs://gcp-public-data-landsat/LC08/01/XXX/YYY/LC08_L1TP_XXXYYY_*.tar.bz .
```

#### 4. **AWS S3**

📍 **Website:** https://registry.opendata.aws/usgs-landsat/

**Features:**
- Landsat data on Amazon S3
- Fast downloads if using AWS
- AWS free tier eligible

---

## Sentinel-2 Data

### Overview

**Sentinel-2** is operated by the European Space Agency (ESA) as part of the Copernicus program.

**Key Characteristics:**
- Resolution: 10m (visible/NIR), 20m (SWIR)
- Temporal coverage: Every 5 days (combined A+B)
- Free and open-source
- More frequent revisit than Landsat
- 12-13 multispectral bands

### Where to Get Sentinel-2 Data

#### 1. **Copernicus Open Access Hub** (RECOMMENDED)

📍 **Website:** https://scihub.copernicus.eu/

**Step-by-Step Guide:**

1. **Create free account:**
   - Sign up at the website
   - Verify email

2. **Log in and search:**
   - Draw area on map or enter coordinates
   - Set date range
   - Click "Search"

3. **Configure filters:**
   - Sentinel-2 platform
   - Processing level: **L2A** (atmospherically corrected) or **L1C** (top-of-atmosphere)
   - Cloud cover: **0-20%** recommended

4. **Select scene:**
   - Choose from search results
   - Preview available

5. **Download:**
   - Full product: 700 MB - 1 GB
   - Processing may take time (queued download)
   - Can download directly or queue for processing

**Sentinel-2 bands for NDVI:**
```
Band 2  - Blue (458-523 nm)        10m resolution
Band 3  - Green (543-578 nm)       10m resolution
Band 4  - Red (650-680 nm)         10m resolution  ← For NDVI
Band 8  - NIR (785-900 nm)         10m resolution  ← For NDVI
Band 11 - SWIR 1 (1565-1655 nm)    20m resolution
Band 12 - SWIR 2 (2100-2280 nm)    20m resolution
```

#### 2. **European Commission's Dataspace**

📍 **Website:** https://dataspace.copernicus.eu/

**Advantages:**
- Modern interface
- Faster downloads than old hub
- Better searching
- Recommended for new projects

**Registration and download:**
```bash
# Using command line tools:
python -m sentinelsat.cli -u username -p password \
  -g area.geojson \
  -s 2024-01-01 -e 2024-01-31 \
  -c "S2" --level L2A
```

#### 3. **Python API: sentinelsat**

📍 **Installation:**
```bash
pip install sentinelsat
```

**Python script to download:**
```python
from sentinelsat import SentinelAPI, read_geojson, geojson_to_wkt
from datetime import date

# Initialize connection
api = SentinelAPI('username', 'password', 'https://apihub.copernicus.eu/apihub')

# Define area of interest
# Option 1: Draw area in WKT format
footprint = 'POLYGON((lat1 lon1, lat2 lon2, lat3 lon3, lat1 lon1))'

# Option 2: Use GeoJSON
footprint = geojson_to_wkt(read_geojson('area.geojson'))

# Search for Sentinel-2 data
products = api.query(
    footprint,
    date=(date(2024, 1, 1), date(2024, 1, 31)),
    platformname='Sentinel-2',
    cloudcoverpercentage=(0, 20),
    processinglevel='L2A'
)

# Download products
api.download_all(products)
```

#### 4. **SentinelHub** (With API key)

📍 **Website:** https://www.sentinel-hub.com/

**Advantages:**
- Direct API access
- Custom processing available
- Easy integration

**Setup:**
```python
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session

# Get access token
client = BackendApplicationClient(client_id=CLIENT_ID)
oauth = OAuth2Session(client=client)
token = oauth.fetch_token(
    token_url='https://services.sentinel-hub.com/oauth/token',
    client_secret=CLIENT_SECRET
)
```

---

## MODIS Data

### Overview

**MODIS** (Moderate Resolution Imaging Spectroradiometer) provides global data with frequent revisit.

**Key Characteristics:**
- Resolution: 250m, 500m, 1km
- Daily global coverage
- Longer historical record (since 2000)
- Good for regional/global analysis

### Where to Get MODIS Data

#### 1. **NASA LP DAAC** (RECOMMENDED)

📍 **Website:** https://lpdaac.usgs.gov/

**Available products:**
- MOD13Q1 (NDVI, 16-day, 250m)
- MYD13Q1 (NDVI, Aqua, 16-day, 250m)
- MOD09GA (Surface reflectance, daily, 500m)

**Steps:**
1. Visit LP DAAC website
2. Search for MODIS product
3. Define area and date range
4. Download as HDF or GeoTIFF

#### 2. **USGS EROS** (Data search)

📍 **Website:** https://earthexplorer.usgs.gov/

Same as Landsat - select MODIS products instead

---

## Comparison of Data Sources

| Feature | Landsat 8/9 | Sentinel-2 | MODIS |
|---------|-----------|----------|-------|
| **Resolution** | 30m | 10-20m | 250m-1km |
| **Revisit Time** | 16 days | 5 days | 1-2 days |
| **Cost** | Free | Free | Free |
| **Historical Data** | Since 1972 | Since 2015 | Since 2000 |
| **Bands** | 11 | 12-13 | 36 |
| **Coverage** | Global | Global | Global |
| **Data Size** | 3-5 GB | 700 MB-1 GB | 50-200 MB |
| **Best For** | Regional studies | High precision | Global monitoring |

**Recommendation:**
- **Start with:** Sentinel-2 (better resolution, faster repeat)
- **Backup option:** Landsat 8/9 (longer history)
- **Global studies:** MODIS (frequent overpass)

---

## How to Search and Download

### Finding the Right Scene

**1. Define your Area of Interest (AOI):**

Get coordinates:
```python
# Using GeoPy to get coordinates
from geopy.geocoders import Nominatim

geolocator = Nominatim(user_agent="my_app")
location = geolocator.geocode("New York, USA")
print(f"Latitude: {location.latitude}, Longitude: {location.longitude}")
```

**2. Check cloud coverage:**
- Aim for < 20% cloud cover for best results
- Seasonal variations (summer = less cloud in many regions)

**3. Select temporal resolution:**
- Monthly: One scene per month for time series
- Seasonal: Spring, summer, fall, winter
- Event-based: Before/after specific events

### Download Workflow

**Manual Download (Simple):**
```
1. Visit USGS Earth Explorer or Copernicus Hub
2. Define area → set date range → filter by cloud cover
3. Select scene → click download
4. Extract downloaded files
5. Use with Green Cover Calculator
```

**Automated Download (Advanced):**

```bash
# Using wget/curl
wget -r --user=username --password=password \
  https://scihub.copernicus.eu/dhus/odata/v1/...

# Using Python sentinelsat
pip install sentinelsat
sentinelsat -u username -p password -g area.geojson \
  -s 2024-01-01 -e 2024-01-31 -c "S2"
```

---

## Data Preprocessing

### Extract Bands

**From Landsat (GeoTIFF files):**

```python
import rasterio
import numpy as np

# Read Band 4 (Red)
with rasterio.open('LC08_L2SP_012345_20240115_20240125_02_T1_SR_B4.TIF') as src:
    red_band = src.read(1)

# Read Band 5 (NIR)
with rasterio.open('LC08_L2SP_012345_20240115_20240125_02_T1_SR_B5.TIF') as src:
    nir_band = src.read(1)

print(f"Red shape: {red_band.shape}")
print(f"NIR shape: {nir_band.shape}")
```

**From Sentinel-2 (JP2000 files):**

```python
from PIL import Image
import numpy as np

# Sentinel-2 bands are usually in separate folders
# B04 = Red (Band 4)
# B08 = NIR (Band 8)

red = np.array(Image.open('GRANULE/IMG_DATA/T30UWE_20240115T103441_B04.jp2'))
nir = np.array(Image.open('GRANULE/IMG_DATA/T30UWE_20240115T103441_B08.jp2'))

print(f"Red shape: {red.shape}")
print(f"NIR shape: {nir.shape}")
```

### Atmospheric Correction

**Landsat Level-2 (already corrected):**
```python
# Level-2A data from USGS is already atmospherically corrected
# Values are surface reflectance (0-10000 scale)
# Divide by 10000 to get 0-1 range
red = red / 10000
nir = nir / 10000
```

**Sentinel-2 Level-2A (already corrected):**
```python
# Level-2A data is already atmospherically corrected
# Values are 0-10000 scale
red = red / 10000
nir = nir / 10000
```

**Sentinel-2 Level-1C (needs correction):**
```python
# Use sen2cor tool or other atmospheric correction
# https://step.esa.int/main/snap-supported-plugins/sen2cor/
# Or use online processing services
```

---

## Working with Downloaded Data

### Organizing Data

**Recommended folder structure:**
```
satellite_data/
├── landsat/
│   ├── 2024-01-15/
│   │   ├── LC08_L2SP_012345_..._B2.TIF
│   │   ├── LC08_L2SP_012345_..._B3.TIF
│   │   ├── LC08_L2SP_012345_..._B4.TIF
│   │   └── LC08_L2SP_012345_..._B5.TIF
│   └── 2024-02-15/
├── sentinel2/
│   ├── 2024-01-15/
│   │   ├── T30UWE_20240115T103441_B02.jp2
│   │   ├── T30UWE_20240115T103441_B04.jp2
│   │   └── T30UWE_20240115T103441_B08.jp2
│   └── 2024-02-15/
└── results/
    ├── ndvi/
    ├── classification/
    └── reports/
```

### Load and Process

**Example: Landsat data**
```python
import sys
from pathlib import Path
sys.path.insert(0, 'src')

from data_loader import SatelliteDataLoader
from ndvi_calculator import NDVICalculator
from visualization import VegetationVisualizer
import rasterio

# Define file paths
scene_dir = "satellite_data/landsat/2024-01-15"

# Load bands using rasterio
with rasterio.open(f"{scene_dir}/LC08_L2SP_012345_..._SR_B4.TIF") as src:
    red = src.read(1) / 10000  # Normalize

with rasterio.open(f"{scene_dir}/LC08_L2SP_012345_..._SR_B5.TIF") as src:
    nir = src.read(1) / 10000  # Normalize

# Calculate NDVI
calc = NDVICalculator(red, nir)
ndvi = calc.calculate_ndvi()

# Get green cover
green_cover, mask = calc.calculate_green_cover(ndvi_threshold=0.4)

# Visualize
visualizer = VegetationVisualizer()
visualizer.plot_ndvi(ndvi, title="Landsat NDVI")

print(f"Green cover: {green_cover:.2f}%")
```

**Example: Sentinel-2 data**
```python
from PIL import Image
import numpy as np
import sys
sys.path.insert(0, 'src')

from ndvi_calculator import NDVICalculator

# Sentinel-2 bands
scene_dir = "satellite_data/sentinel2/2024-01-15/GRANULE/IMG_DATA"

red = np.array(Image.open(f"{scene_dir}/T30UWE_20240115T103441_B04_10m.jp2")) / 10000
nir = np.array(Image.open(f"{scene_dir}/T30UWE_20240115T103441_B08_10m.jp2")) / 10000
blue = np.array(Image.open(f"{scene_dir}/T30UWE_20240115T103441_B02_10m.jp2")) / 10000

# Calculate NDVI and EVI
calc = NDVICalculator(red, nir)
ndvi = calc.calculate_ndvi()
evi = calc.calculate_evi(blue)

print(f"NDVI range: {np.nanmin(ndvi):.3f} to {np.nanmax(ndvi):.3f}")
print(f"EVI range: {np.nanmin(evi):.3f} to {np.nanmax(evi):.3f}")
```

---

## Tips and Best Practices

### Best Practices

**1. Cloud Cover Considerations:**
```
Best practices:
├─ Query with <20% cloud cover threshold
├─ During dry seasons have better visibility
├─ Skip scenes with >50% cloud cover
└─ Use cloud masks where available
```

**2. Seasonal Timing:**
```
Growing season timing (Northern Hemisphere):
├─ Spring (Mar-May): Vegetation greening phase
├─ Summer (Jun-Aug): Maximum vegetation vigor
├─ Fall (Sep-Nov): Senescence and harvesting
└─ Winter (Dec-Feb): Minimal vegetation activity
```

**3. Scene Selection:**
- **Time of day:** Morning scenes often have less haze
- **Viewing angle:** Nadir (straight down) preferred
- **Water bodies:** Cause false negatives in NDVI
- **Mountains:** Avoid extreme slopes

### Troubleshooting Downloads

**Issue: Download Interrupted**
```
Solution:
1. Note the partial download
2. Retry the download (most platforms resume)
3. Verify file integrity after download
```

**Issue: Expired Link**
```
Solution:
1. Search for scene again
2. Generate new download link
3. Download immediately
```

**Issue: Large File Size**
```
Solution:
1. Download only required bands (not full product)
2. Consider MODIS for lower resolution
3. Process in tiles
```

### Tools for Batch Download

**sentinelsat (Python):**
```bash
pip install sentinelsat
sentinelsat -u username -p password \
  -g area.geojson \
  -s 2024-01-01 -e 2024-12-31 \
  -c "S2" --level L2A --download
```

**rasterio (GIS operations):**
```bash
pip install rasterio
```

**SNAP (ESA tool):**
```
Download from: https://step.esa.int/main/download/snap-download/
Useful for Sentinel processing
```

---

## Data Storage and Archive

### Local Storage

**Requirements:**
- 1-2 TB SSD for active projects
- External drives for archive
- Organized folder structure

**Recommended nameing convention:**
```
SENSOR_PRODUCTTYPE_PATHROW_DATE_PROCESSING.tar.gz

Examples:
├── LC08_L2A_012345_20240115_SR.tar.gz
├── S2_L2A_T30UWE_20240115_10m.zip
└── MOD13Q1_NDVI_2024_01.hdf
```

### Cloud Storage Options

**Free tier services:**
- Google Drive: 15 GB
- OneDrive: 5 GB
- Dropbox: 2-3 GB
- AWS S3: 5 GB/month (free tier)

**For research projects:**
- Google Colab + Google Drive
- AWS EC2 instances (free tier 1 year)
- Azure for Students

---

## Quick Reference Links

| Service | URL | Data Type |
|---------|-----|-----------|
| USGS Earth Explorer | https://earthexplorer.usgs.gov/ | Landsat, MODIS |
| Copernicus Hub | https://scihub.copernicus.eu/ | Sentinel-2 |
| Dataspace Copernicus | https://dataspace.copernicus.eu/ | Sentinel-2 (new) |
| NASA LP DAAC | https://lpdaac.usgs.gov/ | MODIS, ASTER |
| Google Cloud | https://cloud.google.com/storage/docs/public-datasets/landsat | Landsat |
| AWS Registry | https://registry.opendata.aws/usgs-landsat/ | Landsat |
| Sentinel Hub | https://www.sentinel-hub.com/ | Sentinel-2 API |

---

## Next Steps

1. **Visit USGS Earth Explorer:** https://earthexplorer.usgs.gov/
2. **Create account and search your area**
3. **Download a small test scene** (< 20% cloud cover)
4. **Extract bands 4 (Red) and 5 (NIR)**
5. **Run with Green Cover Calculator:**
   ```python
   python main.py  # Tests with synthetic data
   ```
6. **Load your real data and analyze**

---

**Last Updated:** February 2024  
**Version:** 1.0.0
