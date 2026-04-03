from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

import numpy as np
import pandas as pd

VectorKey = Tuple[int, int, pd.Timestamp]
VectorValue = Dict[str, float]


@dataclass
class OilFraction:
    mass_fraction: float
    boiling_point: float
    density: float


class OilSpillModel:
    def __init__(
        self,
        water: np.ndarray,
        initial_oil: np.ndarray,
        sea_currents: Dict[VectorKey, VectorValue],
        wind_currents: Dict[VectorKey, VectorValue],
        oil_source: Tuple[int, int],
        initial_spill_days: int,
        alpha: float,
        beta: float,
        movement_diffusion_coefficient: float,
        diagonal_diffusion_coefficient: float,
        temperature_c: float,
        round_precision: int,
    ) -> None:
        if water.shape != initial_oil.shape:
            raise ValueError("water and initial_oil must share the same shape")

        self.height, self.width = water.shape
        self.water = water
        self.oil_mass = initial_oil.astype(float)
        self.sea_currents = sea_currents
        self.wind_currents = wind_currents
        self.oil_source = oil_source
        self.initial_spill_days = initial_spill_days
        self.alpha = alpha
        self.beta = beta
        self.movement_diffusion_coefficient = movement_diffusion_coefficient
        self.diagonal_diffusion_coefficient = diagonal_diffusion_coefficient
        self.temperature_c = temperature_c
        self.round_precision = round_precision
        self.initial_source_mass = float(self.oil_mass[oil_source])

        self.fractions = (
            OilFraction(0.2, 350.0, 800.0),
            OilFraction(0.3, 400.0, 850.0),
            OilFraction(0.5, 450.0, 900.0),
        )

    @staticmethod
    def _vapor_pressure(tb: float, temp_k: float) -> float:
        return 1000.0 * np.exp((4.4 + np.log(tb)) * (1.0 - 1.803 * tb / temp_k) - 0.803 * np.log(tb / temp_k))

    @staticmethod
    def _molar_mass(tb: float, density: float) -> float:
        water_density = 1000.0
        return 2.410e6 * (tb ** 2.847) * (density / water_density) ** 2.130

    def _evaporation_amount(self, cell_mass: float) -> float:
        if cell_mass <= 0:
            return 0.0

        temp_k = self.temperature_c + 273.15
        pressure = 37_000_000.0
        transfer_coeff = 1.25e-3
        gas_constant = 8.314

        total_rate = 0.0
        for fraction in self.fractions:
            vapor_pressure = self._vapor_pressure(fraction.boiling_point, temp_k)
            molar_mass = self._molar_mass(fraction.boiling_point, fraction.density)
            mole_fraction = fraction.mass_fraction / molar_mass
            total_rate += transfer_coeff * molar_mass * vapor_pressure * mole_fraction / (gas_constant * temp_k)

        scaled = min(total_rate * pressure * 1e-12, 0.2)
        return min(cell_mass, cell_mass * scaled)

    def _vector_at(self, vectors: Dict[VectorKey, VectorValue], i: int, j: int, date: pd.Timestamp) -> VectorValue:
        return vectors.get((i, j, date), {"speed": 0.0, "x": 0.0, "y": 0.0})

    def _apply_diffusion(self, source: np.ndarray) -> np.ndarray:
        updated = source.copy()
        orthogonal = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        diagonal = [(-1, -1), (-1, 1), (1, -1), (1, 1)]

        for i in range(1, self.height - 1):
            for j in range(1, self.width - 1):
                if not self.water[i, j]:
                    continue

                center = source[i, j]
                delta = 0.0

                for di, dj in orthogonal:
                    ni, nj = i + di, j + dj
                    if self.water[ni, nj]:
                        delta += self.movement_diffusion_coefficient * (source[ni, nj] - center)

                for di, dj in diagonal:
                    ni, nj = i + di, j + dj
                    if self.water[ni, nj]:
                        delta += self.diagonal_diffusion_coefficient * (source[ni, nj] - center)

                updated[i, j] = max(updated[i, j] + delta, 0.0)

        return updated

    def _apply_advection(self, source: np.ndarray, date: pd.Timestamp) -> np.ndarray:
        moved = source.copy()

        for i in range(1, self.height - 1):
            for j in range(1, self.width - 1):
                if not self.water[i, j]:
                    continue

                mass = moved[i, j]
                if mass <= 0.0:
                    continue

                sea = self._vector_at(self.sea_currents, i, j, date)
                wind = self._vector_at(self.wind_currents, i, j, date)

                vx = self.alpha * sea["x"] * (sea["speed"] / 50.0) + self.beta * wind["x"] * (wind["speed"] / 50.0)
                vy = self.alpha * sea["y"] * (sea["speed"] / 50.0) + self.beta * wind["y"] * (wind["speed"] / 50.0)

                tx = min(abs(vx), 0.35)
                ty = min(abs(vy), 0.35)

                target_j = j + 1 if vx > 0 else j - 1
                target_i = i + 1 if vy > 0 else i - 1

                if self.water[i, target_j] and tx > 0:
                    x_mass = mass * tx
                    moved[i, j] -= x_mass
                    moved[i, target_j] += x_mass
                    mass -= x_mass

                if self.water[target_i, j] and ty > 0:
                    y_mass = mass * ty
                    moved[i, j] -= y_mass
                    moved[target_i, j] += y_mass
                    mass -= y_mass

                if tx > 0 and ty > 0 and self.water[target_i, target_j]:
                    diag_mass = mass * min(tx * ty, 0.15)
                    moved[i, j] -= diag_mass
                    moved[target_i, target_j] += diag_mass

        return np.clip(moved, 0.0, None)

    def step(self, date: pd.Timestamp) -> None:
        if self.initial_spill_days > 0:
            self.oil_mass[self.oil_source] += self.initial_source_mass
            self.initial_spill_days -= 1

        next_oil = self._apply_diffusion(self.oil_mass)
        next_oil = self._apply_advection(next_oil, date)

        for i in range(1, self.height - 1):
            for j in range(1, self.width - 1):
                if not self.water[i, j]:
                    next_oil[i, j] = 0.0
                    continue
                evap = self._evaporation_amount(next_oil[i, j])
                next_oil[i, j] = max(next_oil[i, j] - evap, 0.0)

        next_oil[~self.water] = 0.0
        self.oil_mass = np.round(next_oil, self.round_precision)

    @property
    def total_mass(self) -> float:
        return float(np.sum(self.oil_mass))
