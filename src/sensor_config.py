# src/config.py
"""
Sensor Configuration

Per-sensor constants for radiometric scaling, NoData values, and pixel sizes.
All values are sourced from official product documentation:
  - Landsat Collection 2 Level-2 Science Product Guide (USGS)
  - Sentinel-2 Level-2A Product Specification (ESA)

Adding a new sensor: create a new SensorProfile entry below and register
it in SENSOR_PROFILES.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class SensorProfile:
    """Immutable descriptor for one satellite sensor."""

    name: str

    # Reflectance scaling  →  physical = raw * scale + offset
    # Landsat Collection-2 L2 SR: scale=2.75e-5, offset=-0.2
    # Sentinel-2 L2A:             scale=1e-4,    offset=0.0
    reflectance_scale: float
    reflectance_offset: float

    # Value that represents "no data" in the raw integer arrays
    nodata_value: Optional[float]

    # Valid raw DN range (values outside are masked)
    valid_min: float
    valid_max: float

    # Default ground sampling distance in metres
    default_pixel_size_m: float

    # Supported file extensions (lowercase, with dot)
    supported_extensions: tuple[str, ...] = field(default_factory=tuple)


# ── Sensor profiles ────────────────────────────────────────────────────────────

_LANDSAT_PROFILE = SensorProfile(
    name="Landsat 8/9 Collection-2 Level-2 SR",
    reflectance_scale=2.75e-5,
    reflectance_offset=-0.2,
    nodata_value=0.0,           # fill / masked pixels
    valid_min=1,
    valid_max=65455,            # saturated threshold from product guide
    default_pixel_size_m=30.0,
    supported_extensions=(".tif", ".tiff"),
)

_SENTINEL2_PROFILE = SensorProfile(
    name="Sentinel-2 Level-2A SR",
    reflectance_scale=1e-4,
    reflectance_offset=0.0,
    nodata_value=0.0,
    valid_min=1,
    valid_max=10000,            # surface reflectance is scaled 0–10000
    default_pixel_size_m=10.0, # B02, B04, B08 are all 10 m native
    supported_extensions=(".jp2", ".tif", ".tiff"),
)

# Keys must match the `sensor:` value accepted in config.yaml (lowercase)
SENSOR_PROFILES: dict[str, SensorProfile] = {
    "landsat8":  _LANDSAT_PROFILE,
    "landsat9":  _LANDSAT_PROFILE,   # same Collection-2 scaling
    "sentinel2": _SENTINEL2_PROFILE,
}


def get_profile(sensor_key: str) -> SensorProfile:
    """
    Return the SensorProfile for *sensor_key*.

    Args:
        sensor_key: One of 'landsat8', 'landsat9', 'sentinel2'.

    Raises:
        ValueError: If the sensor key is not recognised.
    """
    key = sensor_key.lower().strip()
    if key not in SENSOR_PROFILES:
        supported = ", ".join(sorted(SENSOR_PROFILES))
        raise ValueError(
            f"Unknown sensor '{sensor_key}'. Supported: {supported}"
        )
    return SENSOR_PROFILES[key]