"""
Example Scripts for Green Cover Analysis
Demonstrates different use cases and workflows.

Run from the project root:
    python examples.py
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import matplotlib
import numpy as np

# ── Non-interactive backend must be set before any pyplot import ───────────────
matplotlib.use("Agg")

# ── Ensure project root is on sys.path (only needed for `python examples.py`) ─
_project_root = Path(__file__).resolve().parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

# ── Clean imports via the package's public API (src/__init__.py) ──────────────
from src import GreenCoverAnalyzer, NDVICalculator, SatelliteDataLoader, VegetationVisualizer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Shared helper ──────────────────────────────────────────────────────────────

def _make_bands(height: int = 100, width: int = 100, seed: int = 42) -> dict:
    """Return synthetic red/NIR/blue bands (avoids repeating boilerplate)."""
    return SatelliteDataLoader().create_synthetic_data(height=height, width=width, seed=seed)


# ── Individual examples ────────────────────────────────────────────────────────

def example_1_basic_ndvi_calculation() -> None:
    """Basic NDVI calculation from two bands."""
    logger.info("=" * 60)
    logger.info("Example 1: Basic NDVI Calculation")
    logger.info("=" * 60)

    bands = _make_bands()
    calc = NDVICalculator(bands["red"], bands["nir"])
    calc.calculate_ndvi()
    stats = calc.get_ndvi_statistics()

    logger.info("NDVI Statistics:")
    for key in ("mean", "median", "min", "max", "std"):
        logger.info("  %-10s %.4f", key.title() + ":", stats[key])


def example_2_green_cover_calculation() -> None:
    """Green cover calculation across a range of NDVI thresholds."""
    logger.info("=" * 60)
    logger.info("Example 2: Green Cover at Different Thresholds")
    logger.info("=" * 60)

    bands = _make_bands()
    calc = NDVICalculator(bands["red"], bands["nir"])
    calc.calculate_ndvi()

    for threshold in (0.2, 0.4, 0.6, 0.8):
        pct, _ = calc.calculate_green_cover(ndvi_threshold=threshold)
        logger.info("  NDVI >= %.1f  →  green cover = %.2f%%", threshold, pct)


def example_3_vegetation_classification() -> None:
    """Classify pixels into named vegetation categories."""
    logger.info("=" * 60)
    logger.info("Example 3: Vegetation Classification")
    logger.info("=" * 60)

    bands = _make_bands()
    calc = NDVICalculator(bands["red"], bands["nir"])
    ndvi = calc.calculate_ndvi()

    _, percentages = GreenCoverAnalyzer(ndvi).classify_vegetation()
    for vtype, pct in percentages.items():
        logger.info("  %-28s %.2f%%", vtype.replace("_", " ").title() + ":", pct)


def example_4_evi_calculation() -> None:
    """Compare NDVI with the Enhanced Vegetation Index (EVI)."""
    logger.info("=" * 60)
    logger.info("Example 4: Enhanced Vegetation Index (EVI)")
    logger.info("=" * 60)

    bands = _make_bands()
    calc = NDVICalculator(bands["red"], bands["nir"])
    ndvi = calc.calculate_ndvi()
    evi = calc.calculate_evi(bands["blue"])

    logger.info("  NDVI mean : %.4f", float(np.nanmean(ndvi)))
    logger.info("  EVI mean  : %.4f", float(np.nanmean(evi)))
    logger.info(
        "  EVI corrects for atmospheric noise and canopy background — "
        "more sensitive than NDVI in high-biomass regions."
    )


def example_5_area_statistics() -> None:
    """Derive real-world area statistics from pixel counts."""
    logger.info("=" * 60)
    logger.info("Example 5: Area Statistics (30 m Landsat pixels)")
    logger.info("=" * 60)

    bands = _make_bands()
    calc = NDVICalculator(bands["red"], bands["nir"])
    ndvi = calc.calculate_ndvi()

    area_stats = GreenCoverAnalyzer(ndvi).get_green_area_stats(pixel_size=30.0)
    logger.info("  Total area  : %.2f km²", area_stats["total_area_km2"])
    logger.info("  Green area  : %.2f km²", area_stats["green_area_km2"])
    logger.info("  Green cover : %.2f%%",   area_stats["green_cover_percentage"])


def example_6_visualization() -> None:
    """Create and save all standard visualisation outputs."""
    logger.info("=" * 60)
    logger.info("Example 6: Visualisations")
    logger.info("=" * 60)

    bands = _make_bands()
    calc = NDVICalculator(bands["red"], bands["nir"])
    ndvi = calc.calculate_ndvi()
    stats = calc.get_ndvi_statistics()
    classification, _ = GreenCoverAnalyzer(ndvi).classify_vegetation()

    viz = VegetationVisualizer(output_directory="output/examples")

    outputs = {
        "NDVI map":      viz.plot_ndvi(ndvi, title="NDVI Map",
                             output_filename="example_ndvi.png"),
        "Classification": viz.plot_vegetation_classification(classification,
                             output_filename="example_classification.png"),
        "Statistics":    viz.plot_statistics_summary(stats,
                             output_filename="example_statistics.png"),
        "RGB Composite": viz.plot_rgb_composite(
                             bands["red"], bands["nir"], bands["blue"],
                             output_filename="example_rgb.png"),
    }

    for label, path in outputs.items():
        if path:
            logger.info("  ✓ %-20s → %s", label, path)
        else:
            logger.warning("  ✗ %-20s  (skipped — matplotlib unavailable?)", label)


# ── Runner ─────────────────────────────────────────────────────────────────────

def run_all_examples() -> None:
    """Execute every example in sequence; log but continue on failure."""
    logger.info("=" * 70)
    logger.info("GREEN COVER CALCULATION — EXAMPLE SCENARIOS")
    logger.info("=" * 70)

    examples = [
        example_1_basic_ndvi_calculation,
        example_2_green_cover_calculation,
        example_3_vegetation_classification,
        example_4_evi_calculation,
        example_5_area_statistics,
        example_6_visualization,
    ]

    for fn in examples:
        try:
            fn()
        except Exception:
            logger.exception("  Error in %s", fn.__name__)

    logger.info("=" * 70)
    logger.info("All examples completed.")
    logger.info("=" * 70)


if __name__ == "__main__":
    run_all_examples()