# config.py
"""
Configuration and constants for the Green Cover Calculator.

Centralising all magic numbers here makes the codebase easier to
maintain and lets callers override defaults without touching core logic.
"""

from pathlib import Path

# ── Directory layout ──────────────────────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
OUTPUT_DIR = ROOT_DIR / "output"

# ── NDVI thresholds ───────────────────────────────────────────────────────────
DEFAULT_NDVI_THRESHOLD: float = 0.4   # minimum NDVI to be classed as vegetated

# Vegetation class boundaries  (lower_inclusive, upper_exclusive)
VEGETATION_CLASSES: dict[str, tuple[float, float]] = {
    "water":               (-1.0,  0.0),
    "bare_soil":           ( 0.0,  0.2),
    "sparse_vegetation":   ( 0.2,  0.4),
    "moderate_vegetation": ( 0.4,  0.6),
    "dense_vegetation":    ( 0.6,  1.0),
}

# ── Satellite / sensor parameters ─────────────────────────────────────────────
DEFAULT_PIXEL_SIZE_M: float = 30.0    # Landsat pixel size in metres

# EVI coefficients (MODIS standard)
EVI_GAIN:  float = 2.5
EVI_C1:    float = 6.0
EVI_C2:    float = 7.5

# ── Output / visualisation ────────────────────────────────────────────────────
DEFAULT_DPI: int = 300
DEFAULT_FIG_SIZE: tuple[int, int] = (12, 10)