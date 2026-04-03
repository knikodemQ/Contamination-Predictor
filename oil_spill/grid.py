from __future__ import annotations

from typing import Tuple

from .config import DomainConfig


def lat_lon_to_index(latitude: float, longitude: float, domain: DomainConfig) -> Tuple[int, int]:
    lat_scale = (latitude - domain.latitude_min) / (domain.latitude_max - domain.latitude_min)
    lon_scale = (longitude - domain.longitude_min) / (domain.longitude_max - domain.longitude_min)

    lat_index = int(lat_scale * (domain.height - 1))
    lon_index = int(lon_scale * (domain.width - 1))

    lat_index = min(max(lat_index, 0), domain.height - 1)
    lon_index = min(max(lon_index, 0), domain.width - 1)
    return lat_index, lon_index
