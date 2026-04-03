from __future__ import annotations

from typing import Dict, Iterable, Tuple

import numpy as np
import pandas as pd
from scipy.interpolate import griddata

VectorKey = Tuple[int, int, pd.Timestamp]
VectorValue = Dict[str, float]


def interpolate_vectors(
    vectors: Dict[VectorKey, VectorValue],
    height: int,
    width: int,
    dates: Iterable[pd.Timestamp],
) -> Dict[VectorKey, VectorValue]:
    interpolated: Dict[VectorKey, VectorValue] = {}
    grid_i, grid_j = np.meshgrid(np.arange(height), np.arange(width), indexing="ij")

    for date in dates:
        points = []
        speed_values = []
        x_values = []
        y_values = []

        for (i, j, vector_date), value in vectors.items():
            if pd.Timestamp(vector_date) != pd.Timestamp(date):
                continue
            points.append((i, j))
            speed_values.append(value["speed"])
            x_values.append(value["x"])
            y_values.append(value["y"])

        if not points:
            continue

        speed_grid = griddata(points, speed_values, (grid_i, grid_j), method="nearest", fill_value=0.0)
        x_grid = griddata(points, x_values, (grid_i, grid_j), method="nearest", fill_value=0.0)
        y_grid = griddata(points, y_values, (grid_i, grid_j), method="nearest", fill_value=0.0)

        for i in range(height):
            for j in range(width):
                interpolated[(i, j, pd.Timestamp(date))] = {
                    "speed": float(speed_grid[i, j]),
                    "x": float(x_grid[i, j]),
                    "y": float(y_grid[i, j]),
                }

    return interpolated
