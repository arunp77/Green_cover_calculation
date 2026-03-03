# Green Cover Calculator from Remote Sensing Data

A comprehensive Python application to calculate vegetation indices and green cover percentages from satellite imagery using remote sensing data.

## Features

- **NDVI Calculation**: Normalized Difference Vegetation Index from red and near-infrared bands
- **EVI Support**: Enhanced Vegetation Index for improved vegetation monitoring
- **Green Cover Analysis**: Calculate percentage of vegetated area
- **Vegetation Classification**: Classify pixels into vegetation categories (water, bare soil, sparse, moderate, dense)
- **Area Statistics**: Calculate vegetated area in square kilometers
- **Visualization**: Create publication-quality maps and charts
- **Data Management**: Store and retrieve analysis results

## Quick Start

### Installation

1. Clone or download the repository
2. Create a Python virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install numpy matplotlib scipy rasterio
```

### Basic Usage

```python
from src.ndvi_calculator import NDVICalculator
from src.data_loader import SatelliteDataLoader
from src.visualization import VegetationVisualizer
import numpy as np

# Load satellite data (red and NIR bands)
loader = SatelliteDataLoader()
bands = loader.create_synthetic_data()  # or load actual data

# Calculate NDVI
calc = NDVICalculator(bands['red'], bands['nir'])
ndvi = calc.calculate_ndvi()

# Calculate green cover
green_cover, green_mask = calc.calculate_green_cover(ndvi_threshold=0.4)

# Visualize results
visualizer = VegetationVisualizer()
visualizer.plot_ndvi(ndvi)
```

## File Structure

```
Green_cover_project/
├── src/
│   ├── __init__.py              # Package initialization
│   ├── ndvi_calculator.py       # NDVI and vegetation indices
│   ├── data_loader.py           # Load satellite data
│   └── visualization.py         # Create visualizations
├── data/                        # Input satellite data
├── output/                      # Results and visualizations
├── tests/                       # Unit tests
├── main.py                      # Main application script
├── examples.py                  # Example usage scenarios
└── README.md                    # This file
```

## Core Modules

### ndvi_calculator.py

**NDVICalculator**: Calculate vegetation indices
- `calculate_ndvi()`: Compute NDVI from red and NIR bands
- `calculate_green_cover()`: Get green cover percentage
- `calculate_evi()`: Enhanced Vegetation Index
- `get_ndvi_statistics()`: Statistical summary

**GreenCoverAnalyzer**: Classify and analyze vegetation
- `classify_vegetation()`: Classify into 5 vegetation categories
- `get_green_area_stats()`: Calculate area statistics

### data_loader.py

**SatelliteDataLoader**: Load and manage satellite data
- `load_geotiff()`: Load GeoTIFF files
- `load_landsat_scene()`: Load Landsat bands
- `create_synthetic_data()`: Generate test data

**VegetationDatabase**: Store analysis results

### visualization.py

**VegetationVisualizer**: Create visualizations
- `plot_ndvi()`: NDVI heatmap
- `plot_vegetation_classification()`: Classification map
- `plot_rgb_composite()`: RGB composite image
- `plot_statistics_summary()`: Statistics charts
- `create_analysis_report()`: Comprehensive report

## Running the Application

### Run Main Analysis
```bash
python main.py
```

This will:
1. Generate synthetic satellite data
2. Calculate NDVI and other indices
3. Classify vegetation
4. Calculate green cover percentage
5. Create visualizations
6. Save results

### Run Example Scenarios
```bash
python examples.py
```

This runs 6 different example use cases demonstrating various features.

## Input Data Format

### Satellite Data Requirements

The application works with multispectral satellite data, particularly:

- **Landsat 8/9**: 
  - Red Band (Band 4)
  - Near-Infrared (Band 5)
  - Blue Band (Band 2) - optional for EVI
  
- **Sentinel-2**:
  - Red Band (Band 4)
  - Near-Infrared (Band 8)
  - Blue Band (Band 2)

### Supported Formats

- GeoTIFF (.tif, .tiff) - requires rasterio
- NumPy arrays (.npy)
- Plain text (.txt, .csv)

## NDVI Formula

```
NDVI = (NIR - Red) / (NIR + Red)
```

Where:
- NIR = Near-Infrared band pixel values
- Red = Red band pixel values

**Interpretation:**
- -1.0 to 0.0: Water and non-vegetated surfaces
- 0.0 to 0.2: Bare soil
- 0.2 to 0.4: Sparse vegetation
- 0.4 to 0.6: Moderate vegetation
- 0.6 to 1.0: Dense vegetation

## EVI Formula

```
EVI = 2.5 * ((NIR - Red) / (NIR + 6*Red - 7.5*Blue + 1))
```

EVI improvements over NDVI:
- Better sensitivity to vegetation changes
- Reduced atmospheric noise
- Accounts for canopy background variations

## Output Files

The application generates:

- **NDVI Maps**: Visualization of vegetation indices
- **Classification Maps**: Vegetation category maps
- **Statistics Charts**: NDVI distribution and summaries
- **RGB Composites**: True/false color composites
- **JSON Results**: Detailed analysis results
- **Reports**: Comprehensive analysis summaries

## Vegetation Classification

The application classifies pixels into 5 categories:

1. **Water**: NDVI < 0.0
2. **Bare Soil**: 0.0 ≤ NDVI < 0.2
3. **Sparse Vegetation**: 0.2 ≤ NDVI < 0.4
4. **Moderate Vegetation**: 0.4 ≤ NDVI < 0.6
5. **Dense Vegetation**: 0.6 ≤ NDVI ≤ 1.0

## Area Calculations

Area statistics are calculated based on pixel size:

```
Area (km²) = Number of Pixels × (Pixel Size in m)² / 1,000,000

Green Cover (%) = Green Pixels / Total Valid Pixels × 100
```

Default pixel size: 30m (Landsat resolution)

## Performance Considerations

- **Memory**: Large images (>5000×5000 pixels) require significant RAM
- **Processing**: Vectorized NumPy operations for speed
- **Visualization**: Matplotlib may be slow for very large images

## Troubleshooting

### ImportError: No module named 'rasterio'

Install optional dependencies:
```bash
pip install rasterio
```

### Matplotlib not found

Visualization requires matplotlib:
```bash
pip install matplotlib
```

### Large NDVI values outside [-1, 1] range

Check data range - may need normalization:
```python
# Normalize to 0-1 range
band = (band - band.min()) / (band.max() - band.min())
```

## Applications

- **Land Use Monitoring**: Track vegetation changes over time
- **Crop Health Assessment**: Monitor agricultural crop development
- **Forest Management**: Assess deforestation and reforestation
- **Climate Studies**: Analyze vegetation patterns and trends
- **Urban Planning**: Identify green spaces
- **Environmental Impact Assessment**: Monitor habitat changes

## Citation

If you use this software in research, please cite:

```
Green Cover Calculator from Remote Sensing Data (2024)
Version 1.0
```

## License

This project is open source and available for educational and research purposes.

## References

- Tucker, C. J. (1979). Red and photographic infrared linear combinations for monitoring vegetation. Remote Sensing of Environment, 8(2), 127-150.
- Huete, A., et al. (2002). Overview of the radiometric and biophysical performance of the MODIS vegetation indices. Remote Sensing of Environment, 83(1), 195-213.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## Support

For questions or issues, please refer to the example code or create an issue in the repository.

---

**Last Updated**: February 2024
**Version**: 1.0.0
