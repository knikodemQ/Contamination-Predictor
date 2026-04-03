from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
import pandas as pd

from oil_spill import DomainConfig, ModelConfig, RunConfig
from oil_spill.data import iter_dates, load_environmental_data
from oil_spill.interpolation import interpolate_vectors
from oil_spill.mask import create_land_mask, create_water_mask
from oil_spill.model import OilSpillModel
from oil_spill.runner import _resolve_source_index


@dataclass(frozen=True)
class SimulationResult:
    source_lat: float
    source_lon: float
    initial_oil_mass: float
    temperature_c: float
    steps: int
    total_mass: float
    max_cell_mass: float
    snapshots: list[dict[str, float]]
    final_grid: list[list[float]]


def _build_demo_model(source_lat: float, source_lon: float, initial_oil_mass: float, temperature_c: float, days: int, steps_per_day: int) -> OilSpillModel:
    domain_cfg = DomainConfig(height=60, width=120)
    model_cfg = ModelConfig(initial_spill_days=max(1, min(days, 3)))
    run_cfg = RunConfig(
        simulation_start="2010-12-01",
        simulation_end=(pd.Timestamp("2010-12-01") + pd.Timedelta(days=days - 1)).strftime("%Y-%m-%d"),
        steps_per_day=steps_per_day,
        save_every_step=False,
    )

    environmental_data = load_environmental_data(
        sea_csv_path=str(run_cfg.sea_currents_csv),
        wind_csv_path=str(run_cfg.wind_currents_csv),
        domain=domain_cfg,
    )
    dates = list(iter_dates(run_cfg.simulation_start, run_cfg.simulation_end))
    sea_currents = interpolate_vectors(environmental_data.sea_currents, domain_cfg.height, domain_cfg.width, dates)
    wind_currents = interpolate_vectors(environmental_data.wind_currents, domain_cfg.height, domain_cfg.width, dates)

    land_mask = create_land_mask(domain_cfg)
    water_mask = create_water_mask(domain_cfg, land_mask)

    oil = np.zeros((domain_cfg.height, domain_cfg.width), dtype=float)
    source_index = _resolve_source_index((source_lat, source_lon), domain_cfg)
    oil[source_index] = initial_oil_mass

    return OilSpillModel(
        water=water_mask,
        initial_oil=oil,
        sea_currents=sea_currents,
        wind_currents=wind_currents,
        oil_source=source_index,
        initial_spill_days=model_cfg.initial_spill_days,
        alpha=model_cfg.alpha,
        beta=model_cfg.beta,
        movement_diffusion_coefficient=model_cfg.movement_diffusion_coefficient,
        diagonal_diffusion_coefficient=model_cfg.diagonal_diffusion_coefficient,
        temperature_c=temperature_c,
        round_precision=model_cfg.round_precision,
    ), dates


def run_preview_simulation(
    source_lat: float,
    source_lon: float,
    initial_oil_mass: float,
    temperature_c: float,
    days: int,
    steps_per_day: int,
) -> dict[str, Any]:
    model, dates = _build_demo_model(
        source_lat=source_lat,
        source_lon=source_lon,
        initial_oil_mass=initial_oil_mass,
        temperature_c=temperature_c,
        days=days,
        steps_per_day=steps_per_day,
    )

    snapshots: list[dict[str, float]] = []
    step_index = 0
    for date in dates:
        for _ in range(steps_per_day):
            model.step(date)
            snapshots.append(
                {
                    "step": float(step_index),
                    "totalMass": float(model.total_mass),
                    "maxCellMass": float(model.oil_mass.max()),
                }
            )
            step_index += 1

    result = SimulationResult(
        source_lat=source_lat,
        source_lon=source_lon,
        initial_oil_mass=initial_oil_mass,
        temperature_c=temperature_c,
        steps=step_index,
        total_mass=float(model.total_mass),
        max_cell_mass=float(model.oil_mass.max()),
        snapshots=snapshots,
        final_grid=model.oil_mass.tolist(),
    )
    return asdict(result)
