from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

from .config import DomainConfig


def setup_axes(domain: DomainConfig):
    fig, ax = plt.subplots(subplot_kw={"projection": ccrs.PlateCarree()}, figsize=(14, 7))
    ax.set_extent(
        [domain.longitude_min, domain.longitude_max, domain.latitude_min, domain.latitude_max],
        crs=ccrs.PlateCarree(),
    )
    return fig, ax


def plot_background(
    ax,
    domain: DomainConfig,
    map_image_path: Path,
    sea_points: Optional[Iterable[tuple[float, float]]] = None,
    wind_points: Optional[Iterable[tuple[float, float]]] = None,
) -> None:
    if map_image_path.exists():
        map_image = Image.open(map_image_path)
        ax.imshow(
            map_image,
            extent=[domain.longitude_min, domain.longitude_max, domain.latitude_min, domain.latitude_max],
            transform=ccrs.PlateCarree(),
            origin="upper",
        )

    land = cfeature.NaturalEarthFeature("physical", "land", "10m", edgecolor="green", facecolor="none")
    ax.add_feature(land)
    ax.add_feature(cfeature.BORDERS, linestyle=":")
    grid = ax.gridlines(draw_labels=True)
    grid.top_labels = False
    grid.right_labels = False

    if sea_points is not None:
        for lat, lon in sea_points:
            ax.plot(lon, lat, marker="o", color="yellow", markersize=1.5, transform=ccrs.PlateCarree())

    if wind_points is not None:
        for lat, lon in wind_points:
            ax.plot(lon, lat, marker="o", color="red", markersize=1.5, transform=ccrs.PlateCarree())


def plot_spill(ax, domain: DomainConfig, oil_mass: np.ndarray, title: str) -> None:
    latitudes = np.linspace(domain.latitude_min, domain.latitude_max, domain.height)
    longitudes = np.linspace(domain.longitude_min, domain.longitude_max, domain.width)
    lon_grid, lat_grid = np.meshgrid(longitudes, latitudes)

    ax.contourf(
        lon_grid,
        lat_grid,
        oil_mass,
        cmap="binary",
        transform=ccrs.PlateCarree(),
        alpha=0.5,
    )
    ax.set_title(title)
