"""
Visualization Module for Remote Sensing Analysis

Creates publication-quality visualisations of vegetation indices.
Matplotlib is treated as an optional dependency; all methods return
None gracefully when it is absent.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional

import numpy as np

from src.config import DEFAULT_DPI, DEFAULT_FIG_SIZE, OUTPUT_DIR

logger = logging.getLogger(__name__)

# Maximum pixels along either axis before downsampling kicks in.
# 2000 × 2000 = 4 M pixels, needs ~122 MB for a float64 RGBA array — safe on any machine.
# A full Sentinel-2 tile is 10980 × 10980 = 120 M pixels → would need 3.6 GB → OOM crash.
_MAX_DISPLAY_PIXELS = 2000


def _downsample(arr: np.ndarray, max_pixels: int = _MAX_DISPLAY_PIXELS) -> np.ndarray:
    """
    Return a spatially downsampled copy of *arr* for display only.

    Uses slice-based subsampling (no interpolation), which is fast and
    preserves the visual appearance of index maps and classification grids.
    The original array passed in is never modified.

    Args:
        arr:        2-D (or 3-D for RGB) numpy array.
        max_pixels: Maximum size along either dimension.

    Returns:
        Downsampled array, or the original if it already fits within max_pixels.
    """
    rows, cols = arr.shape[:2]
    row_step = max(1, rows // max_pixels)
    col_step = max(1, cols // max_pixels)
    if row_step == 1 and col_step == 1:
        return arr          # already small enough — no copy needed
    if arr.ndim == 2:
        downsampled = arr[::row_step, ::col_step]
    else:
        downsampled = arr[::row_step, ::col_step, :]
    logger.debug(
        "Display downsampled: (%d, %d) → (%d, %d)",
        rows, cols, downsampled.shape[0], downsampled.shape[1],
    )
    return downsampled


class VegetationVisualizer:
    """Create and save visualisations for vegetation analysis results."""

    # Class-level colour / label mapping for vegetation classes
    _CLASS_COLORS = ["blue", "brown", "yellow", "orange", "green"]
    _CLASS_LABELS = [
        "Water",
        "Bare Soil",
        "Sparse Vegetation",
        "Moderate Vegetation",
        "Dense Vegetation",
    ]

    def __init__(self, output_directory: str | Path = OUTPUT_DIR) -> None:
        """
        Args:
            output_directory: Directory where all figures are saved.
        """
        self.output_dir = Path(output_directory)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._mpl_available = self._check_matplotlib()

    # ── Public API ─────────────────────────────────────────────────────────────

    def plot_ndvi(
        self,
        ndvi: np.ndarray,
        title: str = "NDVI",
        output_filename: str = "ndvi.png",
        cmap: str = "RdYlGn",
    ) -> Optional[str]:
        """
        Render an NDVI array as a colour-mapped image.

        Args:
            ndvi:            2-D NDVI array.
            title:           Figure title.
            output_filename: Output filename (relative to output_directory).
            cmap:            Matplotlib colormap name.

        Returns:
            Absolute path to the saved image, or None if matplotlib is absent.
        """
        if not self._require_matplotlib("plot_ndvi"):
            return None
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=DEFAULT_FIG_SIZE)
        im = ax.imshow(_downsample(ndvi), cmap=cmap, vmin=-1, vmax=1)
        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.set_xlabel("Pixel column (display-resampled)")
        ax.set_ylabel("Pixel row (display-resampled)")
        plt.colorbar(im, ax=ax, label="NDVI Value")
        return self._save_and_close(fig, output_filename)

    def plot_vegetation_classification(
        self,
        classification: np.ndarray,
        title: str = "Vegetation Classification",
        output_filename: str = "classification.png",
    ) -> Optional[str]:
        """
        Render a classification map with a categorical legend.

        Args:
            classification:  Integer class array (0–4).
            title:           Figure title.
            output_filename: Output filename.

        Returns:
            Absolute path to the saved image, or None.
        """
        if not self._require_matplotlib("plot_vegetation_classification"):
            return None
        import matplotlib.patches as mpatches
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=DEFAULT_FIG_SIZE)
        ax.imshow(_downsample(classification), cmap="tab10", vmin=0, vmax=4)
        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.set_xlabel("Pixel column (display-resampled)")
        ax.set_ylabel("Pixel row (display-resampled)")

        patches = [
            mpatches.Patch(color=self._CLASS_COLORS[i], label=self._CLASS_LABELS[i])
            for i in range(len(self._CLASS_LABELS))
        ]
        ax.legend(handles=patches, loc="upper right")
        return self._save_and_close(fig, output_filename)

    def plot_rgb_composite(
        self,
        red: np.ndarray,
        green: np.ndarray,
        blue: np.ndarray,
        title: str = "RGB Composite",
        output_filename: str = "rgb_composite.png",
    ) -> Optional[str]:
        """
        Render a natural-colour composite from three bands.

        Args:
            red, green, blue: Individual band arrays (will be normalised).
            title:           Figure title.
            output_filename: Output filename.

        Returns:
            Absolute path to the saved image, or None.
        """
        if not self._require_matplotlib("plot_rgb_composite"):
            return None
        import matplotlib.pyplot as plt

        rgb = np.dstack(
            (self._normalize_band(red), self._normalize_band(green), self._normalize_band(blue))
        )
        fig, ax = plt.subplots(figsize=DEFAULT_FIG_SIZE)
        ax.imshow(_downsample(rgb))
        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.set_xlabel("Pixel column (display-resampled)")
        ax.set_ylabel("Pixel row (display-resampled)")
        return self._save_and_close(fig, output_filename)

    def plot_statistics_summary(
        self,
        stats: dict,
        title: str = "NDVI Statistics",
        output_filename: str = "statistics.png",
    ) -> Optional[str]:
        """
        Bar chart of key NDVI statistics.

        Args:
            stats:           Dict from NDVICalculator.get_ndvi_statistics().
            title:           Figure title.
            output_filename: Output filename.

        Returns:
            Absolute path to the saved image, or None.
        """
        if not self._require_matplotlib("plot_statistics_summary"):
            return None
        import matplotlib.pyplot as plt

        stat_names  = ["Mean", "Median", "Min", "Max", "Std Dev"]
        stat_values = [
            stats.get("mean",   0.0),
            stats.get("median", 0.0),
            stats.get("min",    0.0),
            stats.get("max",    0.0),
            stats.get("std",    0.0),
        ]

        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(stat_names, stat_values, color=["blue", "green", "red", "orange", "purple"])
        ax.set_ylabel("NDVI Value", fontsize=12)
        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.set_ylim(-1, 1)
        ax.grid(axis="y", alpha=0.3)

        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2.0, h, f"{h:.3f}", ha="center", va="bottom")

        return self._save_and_close(fig, output_filename)

    def plot_green_cover_timeline(
        self,
        dates: list,
        green_cover: list,
        title: str = "Green Cover Timeline",
        output_filename: str = "timeline.png",
    ) -> Optional[str]:
        """
        Line chart of green-cover percentage over a series of dates.

        Args:
            dates:           Ordered list of date labels.
            green_cover:     Corresponding green-cover percentages (0–100).
            title:           Figure title.
            output_filename: Output filename.

        Returns:
            Absolute path to the saved image, or None.
        """
        if not self._require_matplotlib("plot_green_cover_timeline"):
            return None
        if len(dates) != len(green_cover):
            logger.error("dates and green_cover must have the same length.")
            return None
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(range(len(dates)), green_cover, marker="o", linewidth=2, markersize=8)
        ax.set_xticks(range(len(dates)))
        ax.set_xticklabels([str(d) for d in dates], rotation=45, ha="right")
        ax.set_ylabel("Green Cover (%)", fontsize=12)
        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.grid(alpha=0.3)
        ax.set_ylim(0, 100)
        return self._save_and_close(fig, output_filename)

    def create_analysis_report(
        self,
        ndvi: np.ndarray,
        classification: np.ndarray,
        stats: dict,
        green_cover: float,
        location: str = "Analysis Region",
    ) -> str:
        """
        Generate a full analysis report: figures + text summary.

        Args:
            ndvi:           2-D NDVI array.
            classification: 2-D integer classification array.
            stats:          NDVI statistics dict.
            green_cover:    Green cover percentage.
            location:       Location identifier used for filenames.

        Returns:
            Path to the report directory (as a string).
        """
        safe_name = location.replace(" ", "_")
        report_dir = self.output_dir / f"report_{safe_name}"
        report_dir.mkdir(parents=True, exist_ok=True)

        # Figures saved into the main output dir (consistent with direct calls)
        self.plot_ndvi(ndvi, output_filename=f"{safe_name}_ndvi.png")
        self.plot_vegetation_classification(classification, output_filename=f"{safe_name}_classification.png")
        self.plot_statistics_summary(stats, output_filename=f"{safe_name}_statistics.png")

        # Text summary
        summary_path = report_dir / "summary.txt"
        with summary_path.open("w") as fh:
            fh.write("Green Cover Analysis Report\n")
            fh.write(f"Location: {location}\n")
            fh.write("=" * 50 + "\n\n")
            fh.write(f"Green Cover: {green_cover:.2f}%\n\n")
            fh.write("NDVI Statistics:\n")
            for key, value in stats.items():
                line = f"  {key}: {value:.4f}\n" if isinstance(value, float) else f"  {key}: {value}\n"
                fh.write(line)

        logger.info("Report written to %s.", report_dir)
        return str(report_dir)

    # ── Private helpers ────────────────────────────────────────────────────────

    def _require_matplotlib(self, method_name: str) -> bool:
        if not self._mpl_available:
            logger.warning("%s skipped: matplotlib is not installed.", method_name)
        return self._mpl_available

    def _save_and_close(self, fig, filename: str) -> str:
        """Save figure at high DPI and close it to free memory."""
        import matplotlib.pyplot as plt

        path = self.output_dir / filename
        fig.savefig(path, dpi=DEFAULT_DPI, bbox_inches="tight")
        plt.close(fig)
        logger.debug("Figure saved: %s", path)
        return str(path)

    @staticmethod
    def _normalize_band(band: np.ndarray) -> np.ndarray:
        """Min-max normalise a band array to [0, 1]."""
        lo, hi = np.nanmin(band), np.nanmax(band)
        if hi == lo:
            return np.zeros_like(band, dtype=np.float64)
        return (band - lo) / (hi - lo)

    @staticmethod
    def _check_matplotlib() -> bool:
        try:
            import matplotlib  # noqa: F401
            return True
        except ImportError:
            return False