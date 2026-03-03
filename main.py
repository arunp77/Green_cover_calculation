# main.py
"""
Green Cover Calculator — Main Application

Reads config.yaml, loads real satellite data (Landsat 8/9 or Sentinel-2),
runs the full analysis pipeline including all scientific visualisations,
and groups scenes by location for temporal / change-detection analysis.

Usage:
    python main.py
    python main.py --config path/to/config.yaml
"""

from __future__ import annotations

import argparse
import logging
import sys
from collections import defaultdict
from pathlib import Path
from typing import Optional

import matplotlib
matplotlib.use("Agg")

_project_root = Path(__file__).resolve().parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import numpy as np

from src import (
    GreenCoverAnalyzer,
    NDVICalculator,
    SatelliteDataLoader,
    ScientificVisualizer,
    VegetationDatabase,
    VegetationVisualizer,
)
from src.sensor_config import get_profile

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── Config loader ──────────────────────────────────────────────────────────────

def load_config(config_path: str | Path) -> dict:
    try:
        import yaml
    except ImportError:
        logger.error("PyYAML required.  Install: pip install pyyaml"); sys.exit(1)
    p = Path(config_path)
    if not p.exists():
        logger.error("Config not found: %s", p); sys.exit(1)
    with p.open() as fh:
        cfg = yaml.safe_load(fh)
    logger.info("Config loaded: %s  (%d scene(s))", p, len(cfg.get("scenes", [])))
    return cfg


# ── Per-scene analysis ─────────────────────────────────────────────────────────

def analyse_scene(
    scene_cfg: dict,
    output_dir: str,
    sci_output_dir: str,
    analysis_cfg: dict,
    output_cfg: dict,
) -> Optional[dict]:
    """
    Full pipeline for one scene:
      load → scale → NDVI/EVI/SAVI/MSAVI2/NDWI → classify
      → basic charts → scientific charts → report.

    Returns result dict, or None on failure.
    """
    location: str = scene_cfg.get("location", "Unknown")
    date: str     = scene_cfg.get("date",     "unknown-date")
    sensor: str   = scene_cfg["sensor"]
    profile       = get_profile(sensor)
    pixel_size_m  = scene_cfg.get("pixel_size_m", profile.default_pixel_size_m)

    ndvi_threshold = analysis_cfg.get("ndvi_threshold", 0.4)
    savi_L         = analysis_cfg.get("savi_L",         0.5)

    logger.info("")
    logger.info("═" * 64)
    logger.info("Scene: %s (%s)  sensor=%s", location, date, sensor)
    logger.info("═" * 64)

    # 1. Load bands ─────────────────────────────────────────────────────────
    logger.info("Step 1 — Loading bands …")
    loader = SatelliteDataLoader()
    bands  = loader.load_scene_from_config(scene_cfg)
    red, nir = bands["red"], bands["nir"]
    blue: Optional[np.ndarray] = bands.get("blue")
    swir: Optional[np.ndarray] = bands.get("swir")

    # 2. Vegetation indices ─────────────────────────────────────────────────
    logger.info("Step 2 — Calculating vegetation indices …")
    calc    = NDVICalculator(red, nir)
    indices = calc.calculate_all_indices(
        blue_band=blue,
        swir_band=swir,
        savi_L=savi_L,
    )
    ndvi = indices["ndvi"]
    stats = calc.get_ndvi_statistics()
    logger.info(
        "  NDVI  shape=%s  mean=%.4f  range=[%.4f, %.4f]  valid_px=%d",
        ndvi.shape, stats["mean"], stats["min"], stats["max"], stats["valid_pixels"],
    )

    # 3. Green cover ────────────────────────────────────────────────────────
    logger.info("Step 3 — Green cover …")
    green_pct, _ = calc.calculate_green_cover(ndvi_threshold=ndvi_threshold)
    logger.info("  Green cover: %.2f%%", green_pct)

    # 4. Classify vegetation ────────────────────────────────────────────────
    logger.info("Step 4 — Classifying vegetation …")
    analyzer = GreenCoverAnalyzer(ndvi)
    classification, class_pct = analyzer.classify_vegetation()
    for vtype, pct in class_pct.items():
        logger.info("  %-28s %.2f%%", vtype.replace("_", " ").title() + ":", pct)

    # 5. Area statistics ────────────────────────────────────────────────────
    logger.info("Step 5 — Area statistics (%.0f m/pixel) …", pixel_size_m)
    area_stats = analyzer.get_green_area_stats(pixel_size=pixel_size_m)
    logger.info(
        "  Total=%.2f km²   Green=%.2f km²",
        area_stats["total_area_km2"], area_stats["green_area_km2"],
    )

    # 6. Basic visualisations ───────────────────────────────────────────────
    basic_figures: list[str] = []
    if output_cfg.get("save_visualizations", True):
        logger.info("Step 6 — Basic visualisations …")
        viz  = VegetationVisualizer(output_directory=output_dir)
        safe = _safe(location)

        _add(basic_figures, viz.plot_ndvi(
            ndvi, title=f"NDVI — {location} ({date})",
            output_filename=f"{safe}_{date}_ndvi.png",
        ))
        _add(basic_figures, viz.plot_vegetation_classification(
            classification,
            title=f"Vegetation Classification — {location} ({date})",
            output_filename=f"{safe}_{date}_classification.png",
        ))
        _add(basic_figures, viz.plot_statistics_summary(
            stats, output_filename=f"{safe}_{date}_stats.png",
        ))
        if "evi" in indices:
            _add(basic_figures, viz.plot_ndvi(
                indices["evi"], title=f"EVI — {location} ({date})",
                output_filename=f"{safe}_{date}_evi.png", cmap="viridis",
            ))
        logger.info("  %d basic figure(s) saved.", len(basic_figures))

    # 7. Scientific visualisations ──────────────────────────────────────────
    sci_figures: list[str] = []
    if output_cfg.get("save_scientific_charts", True):
        logger.info("Step 7 — Scientific visualisations …")
        sci_viz = ScientificVisualizer(output_directory=sci_output_dir)
        sci_figures = sci_viz.generate_full_scientific_report(
            bands=bands,
            indices=indices,
            classification=classification,
            location=location,
            date=date,
            ndvi_threshold=ndvi_threshold,
        )

    # 8. Report ─────────────────────────────────────────────────────────────
    report_path: Optional[str] = None
    if output_cfg.get("save_reports", True):
        logger.info("Step 8 — Writing report …")
        viz = VegetationVisualizer(output_directory=output_dir)
        report_path = viz.create_analysis_report(
            ndvi, classification, stats, green_pct, location
        )
        logger.info("  Report → %s", report_path)

    return {
        "location":                  location,
        "date":                      date,
        "sensor":                    sensor,
        "ndvi":                      ndvi,               # kept for temporal analysis
        "classification":            classification,     # kept for temporal analysis
        "indices":                   {k: v for k, v in indices.items() if k != "ndvi"},
        "green_cover_percentage":    green_pct,
        "ndvi_statistics":           stats,
        "vegetation_classification": class_pct,
        "area_statistics":           area_stats,
        "report_path":               report_path,
        "basic_figures":             basic_figures,
        "sci_figures":               sci_figures,
    }


# ── Temporal analysis (across scenes of the same location) ────────────────────

def run_temporal_analysis(
    location: str,
    results: list[dict],
    sci_output_dir: str,
    analysis_cfg: dict,
) -> None:
    """
    Generate temporal and change-detection charts for all scenes of one location.
    Requires ≥ 2 scenes sorted by date.
    """
    if len(results) < 2:
        return

    results_sorted = sorted(results, key=lambda r: r["date"])
    logger.info("")
    logger.info("── Temporal analysis: %s  (%d scenes) ──", location, len(results_sorted))

    sci_viz = ScientificVisualizer(output_directory=sci_output_dir)

    # Build records list expected by time-series methods
    records = [
        {"date": r["date"], "ndvi": r["ndvi"], "classification": r["classification"]}
        for r in results_sorted
    ]

    # NDVI time-series + phenology heatmap
    sci_viz.plot_ndvi_timeseries(records, location=location)
    sci_viz.plot_phenology_heatmap(records, location=location)
    sci_viz.plot_green_cover_timeseries(records, location=location)

    # Pairwise change detection between every consecutive scene pair
    for i in range(len(results_sorted) - 1):
        r1, r2 = results_sorted[i], results_sorted[i + 1]
        ndvi_t1, ndvi_t2 = r1["ndvi"], r2["ndvi"]

        if ndvi_t1.shape != ndvi_t2.shape:
            logger.warning(
                "  Skipping change detection %s→%s: shape mismatch %s vs %s",
                r1["date"], r2["date"], ndvi_t1.shape, ndvi_t2.shape,
            )
            continue

        delta = GreenCoverAnalyzer.compute_ndvi_change(ndvi_t1, ndvi_t2)
        _, summary = GreenCoverAnalyzer.classify_change(
            delta,
            gain_threshold=analysis_cfg.get("change_gain_threshold",  0.1),
            loss_threshold=analysis_cfg.get("change_loss_threshold", -0.1),
        )
        logger.info(
            "  Change %s→%s: loss=%.1f%%  stable=%.1f%%  gain=%.1f%%",
            r1["date"], r2["date"],
            summary["loss_pct"], summary["stable_pct"], summary["gain_pct"],
        )
        sci_viz.plot_change_detection(
            ndvi_t1, ndvi_t2, delta, summary,
            date_t1=r1["date"], date_t2=r2["date"],
            location=location,
        )


# ── Helpers ────────────────────────────────────────────────────────────────────

def _add(lst: list, value: Optional[str]) -> None:
    if value is not None:
        lst.append(value)

def _safe(name: str) -> str:
    return name.replace(" ", "_").replace("/", "-")


# ── Entry point ────────────────────────────────────────────────────────────────

def main() -> list[dict]:
    parser = argparse.ArgumentParser(
        description="Green Cover Calculator — config-driven satellite analysis"
    )
    parser.add_argument("--config", default="config.yaml",
                        help="Path to YAML config (default: config.yaml)")
    args = parser.parse_args()

    cfg          = load_config(args.config)
    output_cfg   = cfg.get("output",   {})
    analysis_cfg = cfg.get("analysis", {})
    scenes       = cfg.get("scenes",   [])

    if not scenes:
        logger.error("No scenes defined in %s.", args.config); sys.exit(1)

    output_dir     = output_cfg.get("directory", "output")
    sci_subdir     = output_cfg.get("scientific_subdirectory", "scientific")
    sci_output_dir = str(Path(output_dir) / sci_subdir)

    db      = VegetationDatabase(db_path=f"{output_dir}/analysis_results.json")
    results = []

    # ── Per-scene loop ─────────────────────────────────────────────────────────
    for i, scene_cfg in enumerate(scenes, 1):
        logger.info("Processing scene %d / %d …", i, len(scenes))
        try:
            result = analyse_scene(
                scene_cfg=scene_cfg,
                output_dir=output_dir,
                sci_output_dir=sci_output_dir,
                analysis_cfg=analysis_cfg,
                output_cfg=output_cfg,
            )
            if result:
                results.append(result)
                db.add_result(
                    location=result["location"],
                    date=result["date"],
                    green_cover=result["green_cover_percentage"],
                    statistics=result["ndvi_statistics"],
                    classification=result["vegetation_classification"],
                )
        except FileNotFoundError as exc:
            logger.error("Skipping '%s': %s", scene_cfg.get("location", "?"), exc)
        except Exception:
            logger.exception("Unexpected error in scene '%s':", scene_cfg.get("location", "?"))

    db.save_results()

    # ── Temporal analysis: group by location ───────────────────────────────────
    by_location: dict[str, list[dict]] = defaultdict(list)
    for r in results:
        by_location[r["location"]].append(r)

    for location, loc_results in by_location.items():
        if len(loc_results) >= 2:
            run_temporal_analysis(
                location=location,
                results=loc_results,
                sci_output_dir=sci_output_dir,
                analysis_cfg=analysis_cfg,
            )

    # ── Summary ────────────────────────────────────────────────────────────────
    logger.info("")
    logger.info("═" * 64)
    logger.info("All done  (%d / %d scenes succeeded)", len(results), len(scenes))
    logger.info("═" * 64)
    for r in results:
        logger.info(
            "  %-35s  green=%.1f%%  area=%.2f km²  sci_figs=%d",
            f"{r['location']} ({r['date']})",
            r["green_cover_percentage"],
            r["area_statistics"]["green_area_km2"],
            len(r.get("sci_figures", [])),
        )
    logger.info("  Basic output   → %s/", output_dir)
    logger.info("  Science charts → %s/", sci_output_dir)

    return results


if __name__ == "__main__":
    main()