from __future__ import annotations

import numpy as np
import rasterio
from cartopy import feature as cfeature
from rasterio.features import geometry_mask
from shapely.geometry import mapping

from .config import DomainConfig


def create_land_mask(domain: DomainConfig) -> np.ndarray:
    land_feature = cfeature.NaturalEarthFeature("physical", "land", "10m")
    land_geometries = list(land_feature.geometries())

    transform = rasterio.transform.from_bounds(
        domain.longitude_min,
        domain.latitude_min,
        domain.longitude_max,
        domain.latitude_max,
        domain.width,
        domain.height,
    )

    land_mask = geometry_mask(
        [mapping(geom) for geom in land_geometries],
        transform=transform,
        invert=True,
        out_shape=(domain.height, domain.width),
    )
    return np.flipud(land_mask)


def create_water_mask(domain: DomainConfig, land_mask: np.ndarray) -> np.ndarray:
    water = np.ones((domain.height, domain.width), dtype=bool)
    water[:, [0, -1]] = False
    water[[0, -1], :] = False
    water[land_mask] = False
    return water
