<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# Green Cover Calculator - Project Instructions

## Project Overview
Python application to calculate vegetation indices and green cover from remote sensing satellite data (Landsat, Sentinel-2).

## Key Components
- **src/ndvi_calculator.py**: NDVI and EVI calculations, vegetation classification
- **src/data_loader.py**: Satellite data loading (GeoTIFF, synthetic data)
- **src/visualization.py**: Visualization and reporting
- **main.py**: Main application workflow
- **examples.py**: Usage examples

## Development Guidelines
1. Use NumPy for efficient array operations
2. Follow PEP 8 code style
3. Add docstrings to all functions
4. Include type hints
5. Test with synthetic data when real data unavailable

## Common Tasks
- **Analyze satellite image**: `python main.py`
- **Run examples**: `python examples.py`
- **Run tests**: `python -m pytest tests/`
- **Install deps**: `pip install -r requirements.txt`

## Data Format
- Input: Red band, NIR band, Blue band (optional) as numpy arrays
- Output: NDVI maps, vegetation classification, green cover %, area statistics

## NDVI Formula: (NIR - Red) / (NIR + Red)
## Green Cover Threshold: Default 0.4 NDVI (moderate vegetation)
