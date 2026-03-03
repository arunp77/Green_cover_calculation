# src/data_loader.py
"""
Data Loader for Remote Sensing Data

Handles loading real satellite imagery (Landsat 8/9 GeoTIFF, Sentinel-2 JP2)
with proper radiometric scaling and NoData masking, plus a synthetic data
generator used exclusively by examples.py.

Key entry point for production use:
    loader = SatelliteDataLoader()
    bands  = loader.load_scene_from_config(scene_cfg)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

from src.config import DATA_DIR, OUTPUT_DIR
from src.sensor_config import SensorProfile, get_profile

logger = logging.getLogger(__name__)


class SatelliteDataLoader:
    """Load and radiometrically correct satellite imagery."""

    def __init__(self, data_directory: str | Path = DATA_DIR) -> None:
        self.data_directory = Path(data_directory)
        self.metadata: dict = {}

    # ── Public: production API ─────────────────────────────────────────────────

    def load_scene_from_config(self, scene_cfg: dict) -> Dict[str, np.ndarray]:
        """
        Load a scene described by one entry from config.yaml.

        Performs:
          1. Raw DN loading via rasterio (or PIL fallback for TIF)
          2. NoData masking  — masked pixels become NaN
          3. Reflectance scaling — physical values in [0, 1]

        Args:
            scene_cfg: Dict with keys 'sensor', 'bands' (red, nir, [blue]).

        Returns:
            Dict 'red', 'nir', and optionally 'blue'.
            All arrays are float64 reflectance with NaN for invalid pixels.
        """
        sensor_key: str = scene_cfg["sensor"]
        band_paths: dict = scene_cfg["bands"]
        profile = get_profile(sensor_key)

        logger.info("Loading scene  sensor=%s", profile.name)

        bands: Dict[str, np.ndarray] = {}
        for band_name in ("red", "nir", "blue"):
            if band_name not in band_paths:
                if band_name == "blue":
                    continue        # blue is optional (needed only for EVI)
                raise KeyError(
                    f"Required band '{band_name}' missing from config scene."
                )
            raw = self._load_raw_band(band_paths[band_name])
            bands[band_name] = self._apply_scaling(raw, profile)
            logger.info(
                "  %-5s  shape=%s  nodata-masked=%d px",
                band_name, bands[band_name].shape,
                int(np.sum(np.isnan(bands[band_name]))),
            )

        self._validate_band_shapes(bands)
        return bands

    def load_landsat_scene(
        self,
        red_band_path: str | Path,
        nir_band_path: str | Path,
        blue_band_path: Optional[str | Path] = None,
        sensor: str = "landsat8",
    ) -> Dict[str, np.ndarray]:
        """
        Load a Landsat scene directly from file paths (no config file needed).

        Args:
            red_band_path:  Path to Band 4 file.
            nir_band_path:  Path to Band 5 file.
            blue_band_path: Optional path to Band 2 file.
            sensor:         'landsat8' or 'landsat9'.
        """
        scene_cfg: dict = {
            "sensor": sensor,
            "bands": {"red": str(red_band_path), "nir": str(nir_band_path)},
        }
        if blue_band_path is not None:
            scene_cfg["bands"]["blue"] = str(blue_band_path)
        return self.load_scene_from_config(scene_cfg)

    def load_sentinel2_scene(
        self,
        red_band_path: str | Path,
        nir_band_path: str | Path,
        blue_band_path: Optional[str | Path] = None,
    ) -> Dict[str, np.ndarray]:
        """
        Load a Sentinel-2 scene directly from file paths.

        Args:
            red_band_path:  Path to B04 file.
            nir_band_path:  Path to B08 file.
            blue_band_path: Optional path to B02 file.
        """
        scene_cfg: dict = {
            "sensor": "sentinel2",
            "bands": {"red": str(red_band_path), "nir": str(nir_band_path)},
        }
        if blue_band_path is not None:
            scene_cfg["bands"]["blue"] = str(blue_band_path)
        return self.load_scene_from_config(scene_cfg)

    def save_data(
        self,
        output_path: str | Path,
        data: np.ndarray,
        metadata: Optional[dict] = None,
    ) -> None:
        """Persist a processed band array with optional sidecar JSON metadata."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if output_path.suffix == ".npy":
            np.save(output_path, data)
        elif output_path.suffix in (".txt", ".csv"):
            np.savetxt(output_path, data)
        else:
            save_path = output_path.with_suffix(".npy")
            np.save(save_path, data)
            logger.warning("Unsupported suffix '%s'; saved as .npy.", output_path.suffix)

        if metadata:
            meta_path = output_path.parent / f"{output_path.stem}_metadata.json"
            with meta_path.open("w") as fh:
                json.dump(metadata, fh, indent=2, default=str)

    # ── Synthetic data (examples.py ONLY — not used by main.py) ───────────────

    def create_synthetic_data(
        self,
        height: int = 100,
        width: int = 100,
        seed: int = 42,
    ) -> Dict[str, np.ndarray]:
        """
        Generate synthetic reflectance data for testing / examples.py.

        Vegetation peaks at image centre and falls off radially.
        Values are already in reflectance range [0, 1] — no scaling needed.

        NOT called by main.py.
        """
        rng = np.random.default_rng(seed)
        y, x = np.ogrid[:height, :width]
        cy, cx = height // 2, width // 2
        norm_dist = np.sqrt((y - cy) ** 2 + (x - cx) ** 2) / np.sqrt(cy ** 2 + cx ** 2)
        noise = lambda: rng.normal(0, 0.02, (height, width))

        red  = np.clip(0.10 + 0.25 * norm_dist + noise(), 0.0, 1.0)
        nir  = np.clip(0.45 - 0.25 * norm_dist + noise(), 0.0, 1.0)
        blue = np.clip(0.08 + 0.20 * norm_dist + noise(), 0.0, 1.0)

        logger.debug("Synthetic data generated: %d×%d seed=%d", height, width, seed)
        return {"red": red, "nir": nir, "blue": blue}

    # ── Private helpers ────────────────────────────────────────────────────────

    def _load_raw_band(self, filepath: str | Path) -> np.ndarray:
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(
                f"Band file not found: {filepath}\n"
                "  Verify the path in config.yaml and that the file is in data/."
            )
        suffix = filepath.suffix.lower()
        if suffix in (".tif", ".tiff", ".jp2"):
            return self._load_with_rasterio(filepath)
        if suffix == ".npy":
            return np.load(filepath)
        if suffix in (".txt", ".csv"):
            return np.loadtxt(filepath)
        raise ValueError(f"Unsupported band format: '{suffix}'")

    def _load_with_rasterio(self, filepath: Path) -> np.ndarray:
        try:
            import rasterio
            with rasterio.open(filepath) as src:
                data = src.read(1).astype(np.float64)
                self.metadata["crs"]       = str(src.crs)
                self.metadata["transform"] = list(src.transform)
                self.metadata["nodata"]    = src.nodata
            logger.debug("rasterio loaded: %s", filepath.name)
            return data
        except ImportError:
            if filepath.suffix.lower() == ".jp2":
                raise ImportError(
                    "rasterio is required to read Sentinel-2 JP2 files.\n"
                    "Install it with:  pip install rasterio"
                )
            logger.warning("rasterio not found; falling back to PIL for %s", filepath.name)
            return self._load_with_pil(filepath)

    @staticmethod
    def _load_with_pil(filepath: Path) -> np.ndarray:
        try:
            from PIL import Image
            return np.array(Image.open(filepath)).astype(np.float64)
        except Exception as exc:
            raise ValueError(f"Could not load '{filepath}': {exc}") from exc

    @staticmethod
    def _apply_scaling(raw: np.ndarray, profile: SensorProfile) -> np.ndarray:
        """
        Mask NoData then apply linear reflectance scaling.

        physical_reflectance = raw * scale + offset
        """
        data = raw.astype(np.float64)

        # Validity mask: exclude nodata and out-of-range DNs
        valid = np.ones(data.shape, dtype=bool)
        if profile.nodata_value is not None:
            valid &= (data != profile.nodata_value)
        valid &= (data >= profile.valid_min) & (data <= profile.valid_max)

        result = np.full_like(data, np.nan)
        result[valid] = data[valid] * profile.reflectance_scale + profile.reflectance_offset
        result = np.clip(result, 0.0, 1.0)
        result[~valid] = np.nan   # restore NaN after clip
        return result

    @staticmethod
    def _validate_band_shapes(bands: Dict[str, np.ndarray]) -> None:
        shapes = {name: arr.shape for name, arr in bands.items()}
        if len(set(shapes.values())) > 1:
            raise ValueError(
                "Band shape mismatch — all bands must be the same size:\n"
                + "\n".join(f"  {k}: {v}" for k, v in shapes.items())
            )


# ── Results database ───────────────────────────────────────────────────────────

class VegetationDatabase:
    """Persist and retrieve vegetation analysis results as JSON."""

    def __init__(self, db_path: str | Path = OUTPUT_DIR / "analysis_results.json") -> None:
        self.db_path = Path(db_path)
        self.results: List[dict] = []

    def add_result(
        self,
        location: str,
        date: str,
        green_cover: float,
        statistics: dict,
        classification: dict,
    ) -> None:
        self.results.append({
            "location":                  location,
            "date":                      date,
            "green_cover_percentage":    green_cover,
            "ndvi_statistics":           statistics,
            "vegetation_classification": classification,
        })
        logger.debug("DB: added result for %s (%s).", location, date)

    def save_results(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self.db_path.open("w") as fh:
            json.dump(self.results, fh, indent=2)
        logger.info("Results saved → %s", self.db_path)

    def load_results(self) -> List[dict]:
        if self.db_path.exists():
            with self.db_path.open("r") as fh:
                self.results = json.load(fh)
            logger.info("Loaded %d result(s) from %s.", len(self.results), self.db_path)
        else:
            logger.warning("DB file not found: %s", self.db_path)
        return self.results