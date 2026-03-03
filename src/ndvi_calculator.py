# src/ndvi_calculator.py
"""
Vegetation Index Calculator

Calculates NDVI, EVI, SAVI, MSAVI2, NDWI and related statistics
from multispectral satellite reflectance bands.

All input arrays must be in physical reflectance units [0, 1] —
i.e. already scaled by SatelliteDataLoader (not raw DNs).
"""

from __future__ import annotations

import logging
from typing import Optional, Tuple

import numpy as np

from src.config import (
    DEFAULT_NDVI_THRESHOLD,
    DEFAULT_PIXEL_SIZE_M,
    EVI_C1,
    EVI_C2,
    EVI_GAIN,
    VEGETATION_CLASSES,
)

logger = logging.getLogger(__name__)


class NDVICalculator:
    """
    Calculate vegetation indices from red, NIR, and optionally blue bands.

    Supported indices
    -----------------
    NDVI  — Normalized Difference Vegetation Index
    EVI   — Enhanced Vegetation Index (needs blue)
    SAVI  — Soil-Adjusted Vegetation Index
    MSAVI2— Modified SAVI (no soil factor needed)
    NDWI  — Normalized Difference Water Index (vegetation water content)
    """

    def __init__(self, red_band: np.ndarray, nir_band: np.ndarray) -> None:
        """
        Args:
            red_band: 2-D reflectance array, Landsat B4 / Sentinel B04.
            nir_band: 2-D reflectance array, Landsat B5 / Sentinel B08.
        """
        if red_band.shape != nir_band.shape:
            raise ValueError(
                f"Band shapes must match: red={red_band.shape}, nir={nir_band.shape}"
            )
        self.red_band = red_band.astype(np.float64)
        self.nir_band = nir_band.astype(np.float64)
        self._ndvi: Optional[np.ndarray] = None
        self._valid_mask: Optional[np.ndarray] = None

    # ── NDVI ───────────────────────────────────────────────────────────────────

    def calculate_ndvi(self) -> np.ndarray:
        """
        NDVI = (NIR − RED) / (NIR + RED)

        Range: −1 to 1. Dense vegetation typically 0.6–0.9.
        Invalid (zero-denominator) pixels → NaN.
        """
        denom = self.nir_band + self.red_band
        self._valid_mask = denom != 0
        ndvi = np.full_like(denom, np.nan)
        ndvi[self._valid_mask] = (
            (self.nir_band[self._valid_mask] - self.red_band[self._valid_mask])
            / denom[self._valid_mask]
        )
        self._ndvi = ndvi
        logger.debug("NDVI: valid pixels=%d", int(self._valid_mask.sum()))
        return ndvi

    def calculate_green_cover(
        self, ndvi_threshold: float = DEFAULT_NDVI_THRESHOLD
    ) -> Tuple[float, np.ndarray]:
        """
        Binary green-cover mask based on NDVI threshold.

        Returns:
            (green_cover_percentage, boolean_mask)
        """
        ndvi = self._ndvi if self._ndvi is not None else self.calculate_ndvi()
        green_mask = ndvi >= ndvi_threshold
        total_valid = int(self._valid_mask.sum())
        green_pixels = int(green_mask.sum())
        pct = (green_pixels / total_valid * 100) if total_valid else 0.0
        logger.debug("Green cover @ threshold=%.2f: %.2f%%", ndvi_threshold, pct)
        return pct, green_mask

    def get_ndvi_statistics(self) -> dict:
        """Statistical summary of valid NDVI values."""
        ndvi = self._ndvi if self._ndvi is not None else self.calculate_ndvi()
        v = ndvi[self._valid_mask]
        return {
            "mean":         float(np.nanmean(v)),
            "std":          float(np.nanstd(v)),
            "min":          float(np.nanmin(v)),
            "max":          float(np.nanmax(v)),
            "median":       float(np.nanmedian(v)),
            "p25":          float(np.nanpercentile(v, 25)),
            "p75":          float(np.nanpercentile(v, 75)),
            "valid_pixels": int(v.size),
        }

    # ── EVI ────────────────────────────────────────────────────────────────────

    def calculate_evi(
        self,
        blue_band: np.ndarray,
        g: float = EVI_GAIN,
        c1: float = EVI_C1,
        c2: float = EVI_C2,
    ) -> np.ndarray:
        """
        EVI = G × (NIR − RED) / (NIR + C1×RED − C2×BLUE + 1)

        Corrects for atmospheric effects and canopy background.
        Less prone to saturation in high-biomass areas than NDVI.
        Requires blue band.
        """
        if blue_band.shape != self.red_band.shape:
            raise ValueError("blue_band shape must match red/NIR bands.")
        blue = blue_band.astype(np.float64)
        denom = self.nir_band + c1 * self.red_band - c2 * blue + 1.0
        valid = denom != 0
        evi = np.full_like(denom, np.nan)
        evi[valid] = g * (self.nir_band[valid] - self.red_band[valid]) / denom[valid]
        return evi

    # ── SAVI ───────────────────────────────────────────────────────────────────

    def calculate_savi(self, L: float = 0.5) -> np.ndarray:
        """
        SAVI = (NIR − RED) / (NIR + RED + L) × (1 + L)

        Soil-Adjusted Vegetation Index. Reduces soil brightness influence,
        useful in arid/semi-arid regions with sparse vegetation.

        Args:
            L: Soil brightness correction factor.
               L=1.0  → bare soil,  L=0.5 → intermediate (default),
               L=0.25 → dense vegetation.

        Range: similar to NDVI but shifted by the L correction.
        """
        denom = self.nir_band + self.red_band + L
        valid = denom != 0
        savi = np.full_like(denom, np.nan)
        savi[valid] = (
            (self.nir_band[valid] - self.red_band[valid]) / denom[valid] * (1 + L)
        )
        logger.debug("SAVI calculated (L=%.2f)", L)
        return savi

    # ── MSAVI2 ─────────────────────────────────────────────────────────────────

    def calculate_msavi2(self) -> np.ndarray:
        """
        MSAVI2 = (2×NIR + 1 − √((2×NIR+1)² − 8×(NIR−RED))) / 2

        Modified Soil-Adjusted Vegetation Index (Qi et al., 1994).
        Self-adjusting — no need to specify L. More accurate than SAVI
        across varying vegetation densities.
        """
        nir, red = self.nir_band, self.red_band
        inner = (2 * nir + 1) ** 2 - 8 * (nir - red)
        # Negative values under sqrt → invalid (can occur at water/cloud edges)
        valid = ~np.isnan(nir) & ~np.isnan(red) & (inner >= 0)
        msavi2 = np.full_like(nir, np.nan)
        msavi2[valid] = (2 * nir[valid] + 1 - np.sqrt(inner[valid])) / 2
        logger.debug("MSAVI2 calculated; invalid sqrt pixels=%d", int((inner < 0).sum()))
        return msavi2

    # ── NDWI (vegetation water content) ───────────────────────────────────────

    def calculate_ndwi(self, swir_band: np.ndarray) -> np.ndarray:
        """
        NDWI = (NIR − SWIR) / (NIR + SWIR)   [Gao, 1996]

        Sensitive to vegetation canopy water content.
        Requires a Short-Wave Infrared band:
          Landsat 8/9: Band 6 (SWIR-1, 1.57 µm)
          Sentinel-2:  Band 11 (SWIR, 1.61 µm)

        Positive values → high water content (healthy vegetation).
        Negative values → dry vegetation / bare soil / built-up.
        """
        if swir_band.shape != self.nir_band.shape:
            raise ValueError("swir_band shape must match nir_band.")
        swir = swir_band.astype(np.float64)
        denom = self.nir_band + swir
        valid = denom != 0
        ndwi = np.full_like(denom, np.nan)
        ndwi[valid] = (self.nir_band[valid] - swir[valid]) / denom[valid]
        return ndwi

    # ── Convenience: compute all available indices at once ─────────────────────

    def calculate_all_indices(
        self,
        blue_band: Optional[np.ndarray] = None,
        swir_band: Optional[np.ndarray] = None,
        savi_L: float = 0.5,
    ) -> dict[str, np.ndarray]:
        """
        Compute every available index and return as a dict.

        Args:
            blue_band: Required for EVI. Skipped if None.
            swir_band: Required for NDWI. Skipped if None.
            savi_L:    Soil correction factor for SAVI.

        Returns:
            Dict mapping index name → 2-D array.
            'ndvi' is always present; others depend on available bands.
        """
        indices: dict[str, np.ndarray] = {
            "ndvi":   self.calculate_ndvi(),
            "savi":   self.calculate_savi(L=savi_L),
            "msavi2": self.calculate_msavi2(),
        }
        if blue_band is not None:
            indices["evi"] = self.calculate_evi(blue_band)
        if swir_band is not None:
            indices["ndwi"] = self.calculate_ndwi(swir_band)

        logger.info("Computed indices: %s", list(indices.keys()))
        return indices


# ── Vegetation classifier ──────────────────────────────────────────────────────

class GreenCoverAnalyzer:
    """Classify, quantify, and compare green cover from vegetation indices."""

    VEGETATION_CLASSES = VEGETATION_CLASSES

    def __init__(self, ndvi: np.ndarray) -> None:
        """
        Args:
            ndvi: 2-D NDVI array; NaN marks invalid/masked pixels.
        """
        self.ndvi = ndvi

    def classify_vegetation(self) -> Tuple[np.ndarray, dict]:
        """
        Assign each pixel to a named vegetation class.

        Returns:
            (classification_map, class_percentages_dict)
        """
        classification = np.zeros_like(self.ndvi, dtype=np.int8)
        class_counts: dict[str, int] = {}
        items = list(self.VEGETATION_CLASSES.items())

        for idx, (name, (lower, upper)) in enumerate(items):
            mask = (
                (self.ndvi >= lower) & (self.ndvi <= upper)
                if idx == len(items) - 1
                else (self.ndvi >= lower) & (self.ndvi < upper)
            )
            classification[mask] = idx
            class_counts[name] = int(mask.sum())

        total_valid = int(np.sum(~np.isnan(self.ndvi)))
        class_percentages = {
            name: (count / total_valid * 100 if total_valid else 0.0)
            for name, count in class_counts.items()
        }
        return classification, class_percentages

    def get_green_area_stats(self, pixel_size: float = DEFAULT_PIXEL_SIZE_M) -> dict:
        """
        Area statistics in km² for vegetated pixels (NDVI ≥ 0.2).

        Args:
            pixel_size: Ground sampling distance in metres.
        """
        _, percentages = self.classify_vegetation()
        valid_mask  = ~np.isnan(self.ndvi)
        green_mask  = (self.ndvi >= 0.2) & valid_mask
        total_px    = int(valid_mask.sum())
        green_px    = int(green_mask.sum())
        px_km2      = (pixel_size ** 2) / 1e6

        return {
            "total_area_km2":         total_px * px_km2,
            "green_area_km2":         green_px * px_km2,
            "green_cover_percentage": (green_px / total_px * 100) if total_px else 0.0,
            "vegetation_breakdown":   percentages,
            "pixel_size_m":           pixel_size,
        }

    # ── Temporal / change-detection helpers ───────────────────────────────────

    @staticmethod
    def compute_ndvi_change(
        ndvi_t1: np.ndarray,
        ndvi_t2: np.ndarray,
    ) -> np.ndarray:
        """
        Pixel-wise NDVI difference: Δ = NDVI_t2 − NDVI_t1.

        Positive → vegetation gain.  Negative → vegetation loss.
        NaN where either scene is invalid.
        """
        if ndvi_t1.shape != ndvi_t2.shape:
            raise ValueError(
                f"Shape mismatch for change detection: {ndvi_t1.shape} vs {ndvi_t2.shape}"
            )
        return ndvi_t2 - ndvi_t1

    @staticmethod
    def classify_change(
        delta: np.ndarray,
        gain_threshold: float = 0.1,
        loss_threshold: float = -0.1,
    ) -> Tuple[np.ndarray, dict]:
        """
        Classify each pixel's NDVI change into gain / stable / loss.

        Args:
            delta:           Output of compute_ndvi_change().
            gain_threshold:  Δ ≥  this → "gain".
            loss_threshold:  Δ ≤  this → "loss". Values between → "stable".

        Returns:
            (change_class_map, summary_dict)
            change_class_map: 0=loss, 1=stable, 2=gain  (NaN → -1)
        """
        change_map = np.full_like(delta, -1, dtype=np.float32)
        change_map[delta <= loss_threshold]  = 0   # loss
        change_map[
            (delta > loss_threshold) & (delta < gain_threshold)
        ] = 1                                       # stable
        change_map[delta >= gain_threshold]  = 2   # gain

        valid = ~np.isnan(delta)
        total = int(valid.sum())
        summary = {
            "loss_pct":   float((change_map[valid] == 0).sum() / total * 100) if total else 0.0,
            "stable_pct": float((change_map[valid] == 1).sum() / total * 100) if total else 0.0,
            "gain_pct":   float((change_map[valid] == 2).sum() / total * 100) if total else 0.0,
            "mean_delta": float(np.nanmean(delta)),
            "gain_threshold":  gain_threshold,
            "loss_threshold":  loss_threshold,
        }
        return change_map, summary