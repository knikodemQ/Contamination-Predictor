from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Tuple

import pandas as pd

from .config import DomainConfig
from .grid import lat_lon_to_index

VectorKey = Tuple[int, int, pd.Timestamp]
VectorValue = Dict[str, float]


@dataclass
class EnvironmentalData:
    sea_currents: Dict[VectorKey, VectorValue]
    wind_currents: Dict[VectorKey, VectorValue]
    sea_points: list[tuple[float, float]]
    wind_points: list[tuple[float, float]]


def _prepare_dataframe(csv_path: str, domain: DomainConfig) -> pd.DataFrame:
    data = pd.read_csv(csv_path)
    data["date"] = pd.to_datetime(data["date"]).dt.normalize()

    mask = (
        (data["latitude"] >= domain.latitude_min)
        & (data["latitude"] <= domain.latitude_max)
        & (data["longitude"] >= domain.longitude_min)
        & (data["longitude"] <= domain.longitude_max)
    )
    data = data.loc[mask].copy()

    indices = data.apply(
        lambda row: lat_lon_to_index(
            latitude=float(row["latitude"]),
            longitude=float(row["longitude"]),
            domain=domain,
        ),
        axis=1,
    )
    data[["lat_index", "lon_index"]] = pd.DataFrame(indices.tolist(), index=data.index)
    return data


def _build_vector_dict(
    data: pd.DataFrame,
    speed_col: str,
    x_col: str,
    y_col: str,
) -> Dict[VectorKey, VectorValue]:
    vectors: Dict[VectorKey, VectorValue] = {}
    grouped = data.groupby(["lat_index", "lon_index", "date"], sort=False)
    for (lat_i, lon_i, date), group in grouped:
        first = group.iloc[0]
        vectors[(int(lat_i), int(lon_i), pd.Timestamp(date))] = {
            "speed": float(first[speed_col]),
            "x": float(first[x_col]),
            "y": float(first[y_col]),
        }
    return vectors


def _extract_points(data: pd.DataFrame) -> list[tuple[float, float]]:
    unique = data[["latitude", "longitude"]].drop_duplicates().itertuples(index=False)
    return [(float(lat), float(lon)) for lat, lon in unique]


def load_environmental_data(
    sea_csv_path: str,
    wind_csv_path: str,
    domain: DomainConfig,
) -> EnvironmentalData:
    sea_df = _prepare_dataframe(sea_csv_path, domain)
    wind_df = _prepare_dataframe(wind_csv_path, domain)

    sea_currents = _build_vector_dict(
        data=sea_df,
        speed_col="sea_water_speed",
        x_col="current_x",
        y_col="current_y",
    )
    wind_currents = _build_vector_dict(
        data=wind_df,
        speed_col="wind_speed",
        x_col="wind_x",
        y_col="wind_y",
    )

    return EnvironmentalData(
        sea_currents=sea_currents,
        wind_currents=wind_currents,
        sea_points=_extract_points(sea_df),
        wind_points=_extract_points(wind_df),
    )


def iter_dates(start: str, end: str) -> Iterable[pd.Timestamp]:
    for value in pd.date_range(start=start, end=end, freq="D"):
        yield pd.Timestamp(value).normalize()
