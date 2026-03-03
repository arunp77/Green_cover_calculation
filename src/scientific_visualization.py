"""
Scientific Visualization Module

Publication-quality charts for remote sensing vegetation analysis,
organised into four scientific categories:

  1. Statistical     — distributions, band correlations, box plots
  2. Multi-index     — NDVI vs EVI vs SAVI vs MSAVI2 comparisons
  3. Temporal        — time-series, change detection, phenology heatmap
  4. Geospatial      — RGB+NDVI overlay, NIR/Red feature space, zonal stats

All methods return the saved file path (str) or None when matplotlib is absent.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import numpy as np

from src.config import DEFAULT_DPI, OUTPUT_DIR

# Import the shared downsampler — keeps display arrays within safe memory bounds
# for large Sentinel-2 scenes (10980 × 10980 = 120 Mpx → 3.6 GB RGBA at float64)
from src.visualization import _downsample

logger = logging.getLogger(__name__)

# ── Colour palettes ────────────────────────────────────────────────────────────
_INDEX_COLOURS = {
    "ndvi":   "#2ecc71",
    "evi":    "#3498db",
    "savi":   "#e67e22",
    "msavi2": "#9b59b6",
    "ndwi":   "#1abc9c",
}

_CLASS_COLOURS = ["#2980b9", "#a04000", "#f1c40f", "#e67e22", "#27ae60"]
_CLASS_LABELS  = [
    "Water", "Bare Soil",
    "Sparse Vegetation", "Moderate Vegetation", "Dense Vegetation",
]

_CHANGE_COLOURS = ["#e74c3c", "#bdc3c7", "#27ae60"]   # loss / stable / gain
_CHANGE_LABELS  = ["Vegetation Loss", "Stable", "Vegetation Gain"]


class ScientificVisualizer:
    """
    Advanced scientific visualisations for vegetation remote sensing.

    Usage
    -----
    viz = ScientificVisualizer(output_directory="output/scientific")

    # Statistical
    viz.plot_ndvi_histogram(ndvi, location="Delhi")
    viz.plot_band_correlation(red, nir, blue)
    viz.plot_index_boxplot({"ndvi": ndvi, "savi": savi})

    # Multi-index
    viz.plot_index_comparison({"ndvi": ndvi, "evi": evi, "savi": savi})
    viz.plot_vegetation_feature_space(red, nir)

    # Temporal
    viz.plot_ndvi_timeseries(records)
    viz.plot_change_detection(ndvi_t1, ndvi_t2, delta, summary)
    viz.plot_phenology_heatmap(records)

    # Geospatial
    viz.plot_rgb_ndvi_overlay(red, green, blue, ndvi)
    viz.plot_zonal_stats(ndvi, zone_mask, zone_names)
    """

    def __init__(self, output_directory: str | Path = OUTPUT_DIR / "scientific") -> None:
        self.output_dir = Path(output_directory)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._mpl_ok = self._check_matplotlib()

    # ══════════════════════════════════════════════════════════════════════════
    # CATEGORY 1 — STATISTICAL
    # ══════════════════════════════════════════════════════════════════════════

    def plot_ndvi_histogram(
        self,
        ndvi: np.ndarray,
        location: str = "Study Area",
        date: str = "",
        bins: int = 100,
        output_filename: Optional[str] = None,
    ) -> Optional[str]:
        """
        NDVI frequency distribution with vegetation class boundary markers.

        Shows the full shape of the distribution — bimodal patterns reveal
        a clear separation between vegetated and non-vegetated pixels.
        Includes kernel density estimate overlay and class boundary vlines.
        """
        if not self._require_mpl("plot_ndvi_histogram"):
            return None
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
        from scipy.stats import gaussian_kde  # scipy is a numpy dependency

        valid = ndvi[~np.isnan(ndvi)].ravel()
        title_date = f" — {date}" if date else ""
        filename = output_filename or f"{_safe(location)}{('_'+date) if date else ''}_ndvi_histogram.png"

        fig, ax = plt.subplots(figsize=(12, 6))

        # Histogram
        counts, edges, patches = ax.hist(
            valid, bins=bins, density=True,
            color="#95a5a6", edgecolor="white", linewidth=0.3, alpha=0.7,
            label="NDVI density",
        )

        # KDE overlay
        if valid.size > 10:
            kde_x = np.linspace(valid.min(), valid.max(), 500)
            kde_y = gaussian_kde(valid)(kde_x)
            ax.plot(kde_x, kde_y, color="#2c3e50", linewidth=2, label="KDE")

        # Vegetation class boundaries
        boundaries = [0.0, 0.2, 0.4, 0.6, 1.0]
        colours    = _CLASS_COLOURS
        labels     = _CLASS_LABELS
        for i, (lo, hi) in enumerate(zip(boundaries[:-1], boundaries[1:])):
            ax.axvspan(lo, hi, alpha=0.10, color=colours[i], zorder=0)
            ax.axvline(lo, color=colours[i], linestyle="--", linewidth=0.8, alpha=0.7)

        ax.axvline(0.0, color="#e74c3c", linewidth=1, linestyle=":")    # water/soil boundary

        # Stats annotation
        ax.axvline(float(np.nanmean(valid)),   color="#e74c3c", linewidth=1.5,
                   linestyle="-", label=f"Mean ({np.nanmean(valid):.3f})")
        ax.axvline(float(np.nanmedian(valid)), color="#f39c12", linewidth=1.5,
                   linestyle="-", label=f"Median ({np.nanmedian(valid):.3f})")

        # Legend for class shading
        class_patches = [
            mpatches.Patch(color=colours[i], alpha=0.4, label=labels[i])
            for i in range(len(labels))
        ]
        leg1 = ax.legend(loc="upper left", fontsize=9)
        ax.add_artist(leg1)
        ax.legend(handles=class_patches, loc="upper right", fontsize=8, title="Veg. classes")

        ax.set_xlabel("NDVI", fontsize=12)
        ax.set_ylabel("Density", fontsize=12)
        ax.set_title(f"NDVI Distribution — {location}{title_date}\n"
                     f"n={valid.size:,} valid pixels", fontsize=13, fontweight="bold")
        ax.set_xlim(-1, 1)
        ax.grid(axis="y", alpha=0.3)
        fig.tight_layout()
        return self._save(fig, filename)

    def plot_band_correlation(
        self,
        red: np.ndarray,
        nir: np.ndarray,
        blue: Optional[np.ndarray] = None,
        location: str = "Study Area",
        output_filename: Optional[str] = None,
    ) -> Optional[str]:
        """
        Band correlation scatter plots (Red vs NIR, Red vs Blue, NIR vs Blue).

        A radiometric sanity check: after correct scaling, vegetation pixels
        should cluster in the top-left of Red/NIR space (low red, high NIR).
        A straight diagonal indicates bare soil or water.
        Uses 2-D histogram (hexbin) to handle large pixel counts efficiently.
        """
        if not self._require_mpl("plot_band_correlation"):
            return None
        import matplotlib.pyplot as plt

        filename = output_filename or f"{_safe(location)}_band_correlation.png"
        pairs = [("red", "nir", red, nir)]
        if blue is not None:
            pairs += [("red", "blue", red, blue), ("nir", "blue", nir, blue)]

        ncols = len(pairs)
        fig, axes = plt.subplots(1, ncols, figsize=(6 * ncols, 5))
        if ncols == 1:
            axes = [axes]

        for ax, (xname, yname, xarr, yarr) in zip(axes, pairs):
            mask = ~np.isnan(xarr) & ~np.isnan(yarr)
            x, y = xarr[mask].ravel(), yarr[mask].ravel()

            # Subsample for speed if very large
            if x.size > 200_000:
                idx = np.random.default_rng(0).choice(x.size, 200_000, replace=False)
                x, y = x[idx], y[idx]

            hb = ax.hexbin(x, y, gridsize=60, cmap="YlOrRd", mincnt=1)
            plt.colorbar(hb, ax=ax, label="Pixel count")

            # 1:1 reference line
            lo = min(x.min(), y.min())
            hi = max(x.max(), y.max())
            ax.plot([lo, hi], [lo, hi], "k--", linewidth=0.8, alpha=0.5, label="1:1")

            # Pearson r
            r = float(np.corrcoef(x, y)[0, 1])
            ax.set_title(f"{xname.upper()} vs {yname.upper()}  (r={r:.3f})", fontsize=11)
            ax.set_xlabel(f"{xname.upper()} reflectance", fontsize=10)
            ax.set_ylabel(f"{yname.upper()} reflectance", fontsize=10)
            ax.legend(fontsize=8)

        fig.suptitle(f"Band Correlations — {location}", fontsize=13, fontweight="bold")
        fig.tight_layout()
        return self._save(fig, filename)

    def plot_index_boxplot(
        self,
        indices: dict[str, np.ndarray],
        location: str = "Study Area",
        date: str = "",
        output_filename: Optional[str] = None,
    ) -> Optional[str]:
        """
        Side-by-side box plots for all computed vegetation indices.

        Provides a compact statistical comparison: median, IQR, outliers.
        Helps quickly see whether SAVI/MSAVI2 reduce the spread relative
        to NDVI (indicating better soil correction).
        """
        if not self._require_mpl("plot_index_boxplot"):
            return None
        import matplotlib.pyplot as plt

        title_date = f" — {date}" if date else ""
        filename = output_filename or f"{_safe(location)}{('_'+date) if date else ''}_index_boxplot.png"

        data, labels, colours = [], [], []
        for name, arr in indices.items():
            valid = arr[~np.isnan(arr)].ravel()
            if valid.size:
                data.append(valid)
                labels.append(name.upper())
                colours.append(_INDEX_COLOURS.get(name, "#7f8c8d"))

        fig, ax = plt.subplots(figsize=(max(8, 2.5 * len(data)), 6))
        bp = ax.boxplot(
            data, patch_artist=True, notch=True,
            medianprops=dict(color="black", linewidth=2),
        )
        for patch, colour in zip(bp["boxes"], colours):
            patch.set_facecolor(colour)
            patch.set_alpha(0.7)

        ax.set_xticklabels(labels, fontsize=11)
        ax.set_ylabel("Index value", fontsize=12)
        ax.set_title(
            f"Vegetation Index Comparison — {location}{title_date}",
            fontsize=13, fontweight="bold",
        )
        ax.grid(axis="y", alpha=0.3)
        ax.axhline(0, color="grey", linewidth=0.8, linestyle="--")
        fig.tight_layout()
        return self._save(fig, filename)

    # ══════════════════════════════════════════════════════════════════════════
    # CATEGORY 2 — MULTI-INDEX COMPARISON
    # ══════════════════════════════════════════════════════════════════════════

    def plot_index_comparison(
        self,
        indices: dict[str, np.ndarray],
        location: str = "Study Area",
        date: str = "",
        output_filename: Optional[str] = None,
    ) -> Optional[str]:
        """
        Spatial map panel: one subplot per index, same colour scale.

        Visualises how each index responds differently to the same landscape.
        NDVI saturates in dense canopy; EVI and MSAVI2 remain more sensitive.
        SAVI shows reduced soil brightness in sparse areas.
        """
        if not self._require_mpl("plot_index_comparison"):
            return None
        import matplotlib.pyplot as plt

        title_date = f" — {date}" if date else ""
        filename = output_filename or f"{_safe(location)}{('_'+date) if date else ''}_index_comparison.png"

        n = len(indices)
        ncols = min(n, 3)
        nrows = (n + ncols - 1) // ncols
        fig, axes = plt.subplots(nrows, ncols, figsize=(6 * ncols, 5 * nrows))
        axes = np.array(axes).ravel()

        for ax, (name, arr) in zip(axes, indices.items()):
            im = ax.imshow(_downsample(arr), cmap="RdYlGn", vmin=-1, vmax=1, interpolation="nearest")
            plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
            mean_val = float(np.nanmean(arr))
            ax.set_title(f"{name.upper()}  (μ={mean_val:.3f})", fontsize=11, fontweight="bold")
            ax.set_xlabel("Pixel X"); ax.set_ylabel("Pixel Y")
            ax.tick_params(labelsize=7)

        # Hide unused subplot slots
        for ax in axes[n:]:
            ax.set_visible(False)

        fig.suptitle(
            f"Vegetation Index Comparison — {location}{title_date}",
            fontsize=14, fontweight="bold", y=1.01,
        )
        fig.tight_layout()
        return self._save(fig, filename)

    def plot_index_scatter(
        self,
        index_x: np.ndarray,
        index_y: np.ndarray,
        name_x: str = "NDVI",
        name_y: str = "EVI",
        location: str = "Study Area",
        classification: Optional[np.ndarray] = None,
        output_filename: Optional[str] = None,
    ) -> Optional[str]:
        """
        Scatter plot of two indices coloured by vegetation class.

        Reveals convergence/divergence between indices.  Points far from
        the diagonal highlight where the two indices disagree — typically
        in high-biomass canopy (NDVI saturates, EVI does not) or over
        bare soil (SAVI suppresses, NDVI inflates).
        """
        if not self._require_mpl("plot_index_scatter"):
            return None
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches

        filename = output_filename or f"{_safe(location)}_{name_x.lower()}_vs_{name_y.lower()}.png"

        valid = ~np.isnan(index_x) & ~np.isnan(index_y)
        x, y = index_x[valid].ravel(), index_y[valid].ravel()

        if x.size > 150_000:
            idx = np.random.default_rng(42).choice(x.size, 150_000, replace=False)
            x, y = x[idx], y[idx]

        # Colour by classification if provided
        if classification is not None:
            c = classification[valid].ravel()
            if x.size < len(c): c = c[:x.size]
            scatter_c = [_CLASS_COLOURS[int(v)] if 0 <= int(v) < 5 else "#95a5a6" for v in c]
        else:
            scatter_c = "#3498db"

        fig, ax = plt.subplots(figsize=(8, 7))
        ax.scatter(x, y, c=scatter_c, s=0.5, alpha=0.4, rasterized=True)

        lo = min(x.min(), y.min())
        hi = max(x.max(), y.max())
        ax.plot([lo, hi], [lo, hi], "k--", linewidth=1, label="1:1 line")

        r = float(np.corrcoef(x, y)[0, 1])
        ax.set_xlabel(name_x, fontsize=12)
        ax.set_ylabel(name_y, fontsize=12)
        ax.set_title(
            f"{name_x} vs {name_y} — {location}  (r={r:.3f})",
            fontsize=12, fontweight="bold",
        )
        if classification is not None:
            patches = [mpatches.Patch(color=_CLASS_COLOURS[i], label=_CLASS_LABELS[i])
                       for i in range(5)]
            ax.legend(handles=patches, loc="upper left", fontsize=8, markerscale=6)
        else:
            ax.legend(fontsize=9)
        ax.grid(alpha=0.2)
        fig.tight_layout()
        return self._save(fig, filename)

    def plot_vegetation_feature_space(
        self,
        red: np.ndarray,
        nir: np.ndarray,
        location: str = "Study Area",
        output_filename: Optional[str] = None,
    ) -> Optional[str]:
        """
        NIR vs Red reflectance 'vegetation feature space'.

        The classic endmember diagram from remote sensing textbooks.
        Vegetation sits in the upper-left (high NIR, low Red).
        Bare soil lines up diagonally (the Soil Line).
        Water clusters near the origin.
        Dense canopy forms a 'vegetation arc' away from the soil line.
        """
        if not self._require_mpl("plot_vegetation_feature_space"):
            return None
        import matplotlib.pyplot as plt

        filename = output_filename or f"{_safe(location)}_feature_space.png"

        mask = ~np.isnan(red) & ~np.isnan(nir)
        r, n = red[mask].ravel(), nir[mask].ravel()
        if r.size > 200_000:
            idx = np.random.default_rng(1).choice(r.size, 200_000, replace=False)
            r, n = r[idx], n[idx]

        fig, ax = plt.subplots(figsize=(8, 7))
        hb = ax.hexbin(r, n, gridsize=70, cmap="viridis", mincnt=1)
        plt.colorbar(hb, ax=ax, label="Pixel density")

        # Soil line (empirical: NIR ≈ 2.4 × Red + 0.03 for many sensors)
        rx = np.linspace(0, r.max(), 200)
        ax.plot(rx, 2.4 * rx + 0.03, "w--", linewidth=1.5, label="Soil line")

        # Annotate endmember regions
        ax.text(0.02, 0.02,  "Water",        fontsize=9,  color="white", style="italic")
        ax.text(0.15, 0.05,  "Bare soil",    fontsize=9,  color="white", style="italic")
        ax.text(0.05, 0.45,  "Dense\nvegetation", fontsize=9, color="white", style="italic")

        ax.set_xlabel("Red reflectance", fontsize=12)
        ax.set_ylabel("NIR reflectance", fontsize=12)
        ax.set_title(
            f"Vegetation Feature Space — {location}\n"
            f"({r.size:,} pixels sampled)",
            fontsize=12, fontweight="bold",
        )
        ax.legend(fontsize=9)
        fig.tight_layout()
        return self._save(fig, filename)

    # ══════════════════════════════════════════════════════════════════════════
    # CATEGORY 3 — TEMPORAL
    # ══════════════════════════════════════════════════════════════════════════

    def plot_ndvi_timeseries(
        self,
        records: list[dict],
        location: str = "Study Area",
        output_filename: Optional[str] = None,
    ) -> Optional[str]:
        """
        Multi-class NDVI time-series with uncertainty bands.

        Args:
            records: List of dicts, each with keys:
                     'date'  (str, YYYY-MM-DD),
                     'ndvi'  (2-D array),
                     'classification' (2-D int array, optional).

        Plots mean ± 1 std for each vegetation class over time.
        Shows seasonal phenology patterns (green-up, peak, senescence).
        """
        if not self._require_mpl("plot_ndvi_timeseries"):
            return None
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        from datetime import datetime

        if len(records) < 2:
            logger.warning("plot_ndvi_timeseries needs ≥ 2 scenes; got %d.", len(records))
            return None

        filename = output_filename or f"{_safe(location)}_ndvi_timeseries.png"

        # Parse dates
        dates = []
        for r in records:
            try:
                dates.append(datetime.strptime(r["date"], "%Y-%m-%d"))
            except Exception:
                logger.warning("Could not parse date '%s'; skipping.", r.get("date"))
                return None

        fig, axes = plt.subplots(2, 1, figsize=(14, 10), sharex=True)

        # ── Panel 1: overall mean NDVI ────────────────────────────────────────
        ax = axes[0]
        means  = [float(np.nanmean(r["ndvi"]))  for r in records]
        stds   = [float(np.nanstd(r["ndvi"]))   for r in records]
        means  = np.array(means); stds = np.array(stds)

        ax.plot(dates, means, "o-", color="#27ae60", linewidth=2, markersize=6,
                label="Mean NDVI")
        ax.fill_between(dates, means - stds, means + stds,
                        color="#27ae60", alpha=0.2, label="± 1 std")
        ax.set_ylabel("NDVI", fontsize=11)
        ax.set_title(f"NDVI Time-Series — {location}", fontsize=13, fontweight="bold")
        ax.legend(fontsize=9); ax.grid(alpha=0.3)
        ax.set_ylim(-0.1, 1.0)

        # ── Panel 2: per-class mean NDVI ──────────────────────────────────────
        ax2 = axes[1]
        class_names = ["water", "bare_soil", "sparse_vegetation",
                       "moderate_vegetation", "dense_vegetation"]

        for cls_idx, (cls_name, colour) in enumerate(zip(class_names, _CLASS_COLOURS)):
            cls_means = []
            for r in records:
                ndvi = r["ndvi"]
                clf  = r.get("classification")
                if clf is not None:
                    mask = (clf == cls_idx) & ~np.isnan(ndvi)
                else:
                    # Fallback: use NDVI thresholds
                    lo_hi = [(- 1, 0), (0, .2), (.2, .4), (.4, .6), (.6, 1)]
                    lo, hi = lo_hi[cls_idx]
                    mask = (ndvi >= lo) & (ndvi < hi) & ~np.isnan(ndvi)
                cls_means.append(float(np.nanmean(ndvi[mask])) if mask.any() else np.nan)

            if not all(np.isnan(cls_means)):
                ax2.plot(dates, cls_means, "o-", color=colour, linewidth=1.8,
                         markersize=5, label=cls_name.replace("_", " ").title())

        ax2.set_ylabel("Mean NDVI per class", fontsize=11)
        ax2.set_xlabel("Date", fontsize=11)
        ax2.legend(fontsize=8, loc="upper left"); ax2.grid(alpha=0.3)
        ax2.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
        ax2.xaxis.set_major_locator(mdates.AutoDateLocator())
        fig.autofmt_xdate(rotation=30, ha="right")
        fig.tight_layout()
        return self._save(fig, filename)

    def plot_change_detection(
        self,
        ndvi_t1: np.ndarray,
        ndvi_t2: np.ndarray,
        delta: np.ndarray,
        change_summary: dict,
        date_t1: str = "T1",
        date_t2: str = "T2",
        location: str = "Study Area",
        output_filename: Optional[str] = None,
    ) -> Optional[str]:
        """
        Four-panel change detection figure.

        Panels: NDVI at T1  |  NDVI at T2  |  ΔNDVI map  |  Change class map
        Δ map uses a diverging colormap (red=loss, white=stable, green=gain).
        """
        if not self._require_mpl("plot_change_detection"):
            return None
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches

        filename = output_filename or (
            f"{_safe(location)}_{date_t1}_to_{date_t2}_change.png"
        )

        fig, axes = plt.subplots(1, 4, figsize=(22, 6))

        # T1 NDVI
        im0 = axes[0].imshow(_downsample(ndvi_t1), cmap="RdYlGn", vmin=-1, vmax=1)
        axes[0].set_title(f"NDVI  {date_t1}", fontsize=11)
        plt.colorbar(im0, ax=axes[0], fraction=0.046)

        # T2 NDVI
        im1 = axes[1].imshow(_downsample(ndvi_t2), cmap="RdYlGn", vmin=-1, vmax=1)
        axes[1].set_title(f"NDVI  {date_t2}", fontsize=11)
        plt.colorbar(im1, ax=axes[1], fraction=0.046)

        # ΔNDVI
        abs_max = float(np.nanpercentile(np.abs(delta[~np.isnan(delta)]), 98))
        im2 = axes[2].imshow(_downsample(delta), cmap="RdBu", vmin=-abs_max, vmax=abs_max)
        axes[2].set_title(f"ΔNDVI  (μ={change_summary['mean_delta']:+.3f})", fontsize=11)
        plt.colorbar(im2, ax=axes[2], fraction=0.046, label="ΔNDVI")

        # Change class map
        from matplotlib.colors import ListedColormap
        cmap_change = ListedColormap(_CHANGE_COLOURS)
        # Map: -1 (NaN/invalid) → show as white via masking
        change_display = np.where(delta < 0, 0, np.where(delta == 0, 1, 2))
        # Use actual classify_change output if passed as float array
        im3 = axes[3].imshow(_downsample(change_display), cmap=cmap_change, vmin=0, vmax=2,
                             interpolation="nearest")
        axes[3].set_title("Change Classification", fontsize=11)
        patches = [mpatches.Patch(color=_CHANGE_COLOURS[i], label=_CHANGE_LABELS[i])
                   for i in range(3)]
        axes[3].legend(handles=patches, loc="lower right", fontsize=7)

        loss_t  = change_summary["loss_threshold"]
        gain_t  = change_summary["gain_threshold"]
        subtitle = (
            f"Loss (ΔNDVI ≤ {loss_t})={change_summary['loss_pct']:.1f}%  |  "
            f"Stable={change_summary['stable_pct']:.1f}%  |  "
            f"Gain (ΔNDVI ≥ {gain_t})={change_summary['gain_pct']:.1f}%"
        )
        fig.suptitle(
            f"Change Detection — {location}  ({date_t1} → {date_t2})\n{subtitle}",
            fontsize=12, fontweight="bold",
        )
        for ax in axes:
            ax.set_xlabel("Pixel X"); ax.set_ylabel("Pixel Y")
            ax.tick_params(labelsize=7)
        fig.tight_layout()
        return self._save(fig, filename)

    def plot_phenology_heatmap(
        self,
        records: list[dict],
        location: str = "Study Area",
        output_filename: Optional[str] = None,
    ) -> Optional[str]:
        """
        Phenology heatmap: mean NDVI per vegetation class × acquisition date.

        Rows = vegetation classes.  Columns = dates.  Cell value = mean NDVI.
        Reveals seasonal green-up and senescence patterns per land cover type.
        Requires ≥ 3 scenes.
        """
        if not self._require_mpl("plot_phenology_heatmap"):
            return None
        import matplotlib.pyplot as plt

        if len(records) < 3:
            logger.warning("plot_phenology_heatmap needs ≥ 3 scenes; got %d.", len(records))
            return None

        filename = output_filename or f"{_safe(location)}_phenology_heatmap.png"

        class_names = ["Water", "Bare Soil", "Sparse Veg.",
                       "Moderate Veg.", "Dense Veg."]
        lo_hi = [(-1, 0), (0, .2), (.2, .4), (.4, .6), (.6, 1)]

        dates   = [r["date"] for r in records]
        matrix  = np.full((len(class_names), len(records)), np.nan)

        for j, r in enumerate(records):
            ndvi = r["ndvi"]
            for i, (lo, hi) in enumerate(lo_hi):
                mask = (ndvi >= lo) & (ndvi < hi) & ~np.isnan(ndvi)
                if mask.any():
                    matrix[i, j] = float(np.nanmean(ndvi[mask]))

        fig, ax = plt.subplots(figsize=(max(10, 2 * len(records)), 5))
        im = ax.imshow(matrix, cmap="RdYlGn", vmin=-0.2, vmax=0.9, aspect="auto")
        plt.colorbar(im, ax=ax, label="Mean NDVI")

        ax.set_xticks(range(len(dates)))
        ax.set_xticklabels(dates, rotation=40, ha="right", fontsize=9)
        ax.set_yticks(range(len(class_names)))
        ax.set_yticklabels(class_names, fontsize=10)

        # Annotate cells
        for i in range(len(class_names)):
            for j in range(len(records)):
                val = matrix[i, j]
                if not np.isnan(val):
                    ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                            fontsize=7, color="black" if abs(val) < 0.6 else "white")

        ax.set_title(
            f"Phenology Heatmap — {location}\n"
            f"Mean NDVI per vegetation class over time",
            fontsize=12, fontweight="bold",
        )
        fig.tight_layout()
        return self._save(fig, filename)

    def plot_green_cover_timeseries(
        self,
        records: list[dict],
        location: str = "Study Area",
        ndvi_threshold: float = 0.4,
        output_filename: Optional[str] = None,
    ) -> Optional[str]:
        """
        Green cover percentage over time with stacked area chart by class.

        Combines a line chart (total green cover %) with a stacked area
        showing the proportion from each vegetation density class.
        """
        if not self._require_mpl("plot_green_cover_timeseries"):
            return None
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        from datetime import datetime

        if len(records) < 2:
            return None

        filename = output_filename or f"{_safe(location)}_greencover_timeseries.png"

        dates = [datetime.strptime(r["date"], "%Y-%m-%d") for r in records]
        lo_hi_names = [
            (0.2, 0.4, "Sparse Veg.", _CLASS_COLOURS[2]),
            (0.4, 0.6, "Moderate Veg.", _CLASS_COLOURS[3]),
            (0.6, 1.0, "Dense Veg.", _CLASS_COLOURS[4]),
        ]

        fig, axes = plt.subplots(2, 1, figsize=(13, 9), sharex=True)

        # ── Panel 1: total green cover line ───────────────────────────────────
        ax = axes[0]
        total_green = []
        for r in records:
            ndvi = r["ndvi"]
            valid = ~np.isnan(ndvi)
            green = (ndvi >= ndvi_threshold) & valid
            pct = float(green.sum() / valid.sum() * 100) if valid.any() else 0.0
            total_green.append(pct)

        ax.plot(dates, total_green, "o-", color="#27ae60", linewidth=2.5,
                markersize=7, label=f"Green cover (NDVI ≥ {ndvi_threshold})")
        ax.fill_between(dates, 0, total_green, color="#27ae60", alpha=0.15)
        ax.set_ylabel("Green Cover (%)", fontsize=11)
        ax.set_title(f"Green Cover Time-Series — {location}", fontsize=13, fontweight="bold")
        ax.legend(fontsize=9); ax.grid(alpha=0.3)
        ax.set_ylim(0, 100)

        # ── Panel 2: stacked proportions by density class ─────────────────────
        ax2 = axes[1]
        class_pcts = []
        for lo, hi, name, colour in lo_hi_names:
            pcts = []
            for r in records:
                ndvi = r["ndvi"]
                valid = ~np.isnan(ndvi)
                cls   = (ndvi >= lo) & (ndvi < hi) & valid
                pcts.append(float(cls.sum() / valid.sum() * 100) if valid.any() else 0.0)
            class_pcts.append((pcts, name, colour))

        bottom = np.zeros(len(records))
        for pcts, name, colour in class_pcts:
            ax2.fill_between(dates, bottom, bottom + np.array(pcts),
                             alpha=0.75, color=colour, label=name, step="mid")
            bottom += np.array(pcts)

        ax2.set_ylabel("% of total valid pixels", fontsize=11)
        ax2.set_xlabel("Date", fontsize=11)
        ax2.legend(fontsize=8, loc="upper left"); ax2.grid(alpha=0.2)
        ax2.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
        ax2.xaxis.set_major_locator(mdates.AutoDateLocator())
        fig.autofmt_xdate(rotation=30, ha="right")
        fig.tight_layout()
        return self._save(fig, filename)

    # ══════════════════════════════════════════════════════════════════════════
    # CATEGORY 4 — GEOSPATIAL
    # ══════════════════════════════════════════════════════════════════════════

    def plot_rgb_ndvi_overlay(
        self,
        red: np.ndarray,
        green: np.ndarray,
        blue: np.ndarray,
        ndvi: np.ndarray,
        location: str = "Study Area",
        date: str = "",
        ndvi_threshold: float = 0.4,
        output_filename: Optional[str] = None,
    ) -> Optional[str]:
        """
        True-colour RGB composite alongside NDVI overlay.

        Left: natural-colour composite.
        Right: RGB with NDVI > threshold highlighted in a semi-transparent
               green overlay — shows exactly where vegetation is relative to
               roads, rivers, and urban areas visible in the RGB.
        """
        if not self._require_mpl("plot_rgb_ndvi_overlay"):
            return None
        import matplotlib.pyplot as plt

        title_date = f" — {date}" if date else ""
        filename = output_filename or f"{_safe(location)}{('_'+date) if date else ''}_rgb_ndvi_overlay.png"

        def norm(b: np.ndarray) -> np.ndarray:
            lo, hi = np.nanpercentile(b, 2), np.nanpercentile(b, 98)
            return np.clip((b - lo) / (hi - lo + 1e-9), 0, 1)

        rgb = np.dstack([norm(red), norm(green), norm(blue)])

        # NDVI overlay: green channel boost where vegetated
        overlay = rgb.copy()
        veg_mask = ndvi >= ndvi_threshold
        overlay[veg_mask, 0] = overlay[veg_mask, 0] * 0.3          # suppress red
        overlay[veg_mask, 1] = np.clip(overlay[veg_mask, 1] + 0.4, 0, 1)  # boost green
        overlay[veg_mask, 2] = overlay[veg_mask, 2] * 0.3          # suppress blue

        fig, axes = plt.subplots(1, 2, figsize=(16, 7))
        axes[0].imshow(_downsample(rgb));     axes[0].set_title("True Colour (RGB)", fontsize=12)
        axes[1].imshow(_downsample(overlay)); axes[1].set_title(
            f"RGB + Vegetation Overlay (NDVI ≥ {ndvi_threshold})", fontsize=12
        )
        for ax in axes:
            ax.set_xlabel("Pixel X"); ax.set_ylabel("Pixel Y")
            ax.tick_params(labelsize=7)

        fig.suptitle(
            f"RGB / Vegetation Overlay — {location}{title_date}",
            fontsize=13, fontweight="bold",
        )
        fig.tight_layout()
        return self._save(fig, filename)

    def plot_zonal_stats(
        self,
        ndvi: np.ndarray,
        zone_mask: np.ndarray,
        zone_names: list[str],
        location: str = "Study Area",
        date: str = "",
        output_filename: Optional[str] = None,
    ) -> Optional[str]:
        """
        NDVI zonal statistics bar chart + zone map.

        Args:
            ndvi:       2-D NDVI array.
            zone_mask:  Integer array (same shape), value = zone index (0-based).
                        -1 or NaN → outside all zones.
            zone_names: Names for zones 0, 1, 2, …

        Computes mean, median, and std NDVI per zone.
        Useful for comparing green cover across administrative districts,
        land-use categories, or buffer rings around a city centre.
        """
        if not self._require_mpl("plot_zonal_stats"):
            return None
        import matplotlib.pyplot as plt

        title_date = f" — {date}" if date else ""
        filename = output_filename or f"{_safe(location)}{('_'+date) if date else ''}_zonal_stats.png"

        n_zones = len(zone_names)
        means, medians, stds = [], [], []

        for z in range(n_zones):
            mask = (zone_mask == z) & ~np.isnan(ndvi)
            vals = ndvi[mask]
            if vals.size:
                means.append(float(np.nanmean(vals)))
                medians.append(float(np.nanmedian(vals)))
                stds.append(float(np.nanstd(vals)))
            else:
                means.append(np.nan); medians.append(np.nan); stds.append(np.nan)

        x = np.arange(n_zones)
        fig, axes = plt.subplots(1, 2, figsize=(16, 6))

        # Bar chart
        ax = axes[0]
        bars = ax.bar(x - 0.2, means,   0.35, label="Mean",   color="#27ae60", alpha=0.8)
        ax.bar(x + 0.15, medians, 0.2,  label="Median", color="#2980b9", alpha=0.8)
        ax.errorbar(x - 0.2, means, yerr=stds, fmt="none",
                    color="#2c3e50", capsize=4, linewidth=1.2, label="± 1 std")
        ax.set_xticks(x); ax.set_xticklabels(zone_names, rotation=30, ha="right", fontsize=9)
        ax.set_ylabel("NDVI", fontsize=11)
        ax.set_title("Zonal NDVI Statistics", fontsize=12, fontweight="bold")
        ax.legend(fontsize=9); ax.grid(axis="y", alpha=0.3)
        ax.set_ylim(0, 1)

        # Zone map
        ax2 = axes[1]
        from matplotlib.colors import ListedColormap
        zone_cmap = plt.cm.get_cmap("tab10", n_zones)
        zone_display = np.where(zone_mask >= 0, zone_mask, np.nan)
        im = ax2.imshow(_downsample(zone_display), cmap=zone_cmap, vmin=0, vmax=n_zones - 1,
                        interpolation="nearest")
        cbar = plt.colorbar(im, ax=ax2, ticks=range(n_zones), fraction=0.046)
        cbar.ax.set_yticklabels(zone_names, fontsize=8)
        ax2.set_title("Zone Map", fontsize=12, fontweight="bold")
        ax2.set_xlabel("Pixel X"); ax2.set_ylabel("Pixel Y")

        fig.suptitle(
            f"Zonal NDVI Analysis — {location}{title_date}",
            fontsize=13, fontweight="bold",
        )
        fig.tight_layout()
        return self._save(fig, filename)

    def plot_spatial_variability(
        self,
        ndvi: np.ndarray,
        window_size: int = 15,
        location: str = "Study Area",
        date: str = "",
        output_filename: Optional[str] = None,
    ) -> Optional[str]:
        """
        Local coefficient of variation (CV) map.

        CV = local_std / |local_mean| computed over a sliding window.
        High CV → spatially heterogeneous areas (forest edges, fragmented cover).
        Low CV  → homogeneous patches (dense forest, bare soil, water bodies).
        Useful for mapping fragmentation and ecotones.
        """
        if not self._require_mpl("plot_spatial_variability"):
            return None
        import matplotlib.pyplot as plt
        from scipy.ndimage import generic_filter

        title_date = f" — {date}" if date else ""
        filename = output_filename or f"{_safe(location)}{('_'+date) if date else ''}_spatial_cv.png"

        # Fill NaN for filter (restore after)
        ndvi_filled = np.where(np.isnan(ndvi), 0.0, ndvi)

        def local_cv(patch: np.ndarray) -> float:
            m = np.mean(patch)
            return np.std(patch) / abs(m) if abs(m) > 0.01 else 0.0

        logger.info("Computing spatial CV (window=%d px) — may take a moment …", window_size)
        cv_map = generic_filter(ndvi_filled, local_cv, size=window_size)
        cv_map[np.isnan(ndvi)] = np.nan

        fig, axes = plt.subplots(1, 2, figsize=(15, 6))

        im0 = axes[0].imshow(_downsample(ndvi), cmap="RdYlGn", vmin=-1, vmax=1)
        axes[0].set_title("NDVI", fontsize=12)
        plt.colorbar(im0, ax=axes[0], fraction=0.046)

        im1 = axes[1].imshow(_downsample(cv_map), cmap="hot_r",
                             vmin=0, vmax=float(np.nanpercentile(cv_map, 95)))
        axes[1].set_title(f"Local CV  (window={window_size}px)", fontsize=12)
        plt.colorbar(im1, ax=axes[1], fraction=0.046, label="CV")

        for ax in axes:
            ax.set_xlabel("Pixel X"); ax.set_ylabel("Pixel Y")
            ax.tick_params(labelsize=7)

        fig.suptitle(
            f"Spatial Variability — {location}{title_date}",
            fontsize=13, fontweight="bold",
        )
        fig.tight_layout()
        return self._save(fig, filename)

    # ══════════════════════════════════════════════════════════════════════════
    # CONVENIENCE: run all charts for one scene in one call
    # ══════════════════════════════════════════════════════════════════════════

    def generate_full_scientific_report(
        self,
        bands: dict[str, np.ndarray],
        indices: dict[str, np.ndarray],
        classification: np.ndarray,
        location: str,
        date: str,
        ndvi_threshold: float = 0.4,
    ) -> list[str]:
        """
        Generate every applicable single-scene chart and return saved paths.

        Args:
            bands:          Dict with 'red', 'nir', and optionally 'blue'.
            indices:        Dict from NDVICalculator.calculate_all_indices().
            classification: 2-D classification map.
            location:       Location label.
            date:           Acquisition date string.

        Returns:
            List of file paths for all generated figures.
        """
        saved: list[str] = []
        ndvi = indices["ndvi"]
        red, nir = bands["red"], bands["nir"]
        blue = bands.get("blue")

        def _add(path: Optional[str]) -> None:
            if path:
                saved.append(path)
                logger.info("  ✓  %s", Path(path).name)

        logger.info("Generating full scientific report — %s (%s)", location, date)

        # Statistical
        _add(self.plot_ndvi_histogram(ndvi,   location=location, date=date))
        _add(self.plot_index_boxplot(indices, location=location, date=date))
        _add(self.plot_band_correlation(red, nir, blue, location=location))

        # Multi-index
        _add(self.plot_index_comparison(indices, location=location, date=date))
        _add(self.plot_vegetation_feature_space(red, nir, location=location))
        if "evi" in indices:
            _add(self.plot_index_scatter(ndvi, indices["evi"], "NDVI", "EVI",
                                         location=location, classification=classification))
        if "savi" in indices:
            _add(self.plot_index_scatter(ndvi, indices["savi"], "NDVI", "SAVI",
                                         location=location, classification=classification))

        # Geospatial
        if blue is not None:
            _add(self.plot_rgb_ndvi_overlay(red, blue, blue, ndvi,
                                             location=location, date=date,
                                             ndvi_threshold=ndvi_threshold))
        _add(self.plot_spatial_variability(ndvi, location=location, date=date))

        logger.info("%d scientific figure(s) saved.", len(saved))
        return saved

    # ══════════════════════════════════════════════════════════════════════════
    # PRIVATE HELPERS
    # ══════════════════════════════════════════════════════════════════════════

    def _save(self, fig, filename: str) -> str:
        import matplotlib.pyplot as plt
        path = self.output_dir / filename
        fig.savefig(path, dpi=DEFAULT_DPI, bbox_inches="tight")
        plt.close(fig)
        return str(path)

    def _require_mpl(self, method: str) -> bool:
        if not self._mpl_ok:
            logger.warning("%s skipped: matplotlib not available.", method)
        return self._mpl_ok

    @staticmethod
    def _check_matplotlib() -> bool:
        try:
            import matplotlib  # noqa: F401
            return True
        except ImportError:
            return False


def _safe(name: str) -> str:
    """Convert a location name to a filesystem-safe string."""
    return name.replace(" ", "_").replace("/", "-")