from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np

from .config import DomainConfig, ModelConfig, RunConfig
from .data import iter_dates, load_environmental_data
from .interpolation import interpolate_vectors
from .mask import create_land_mask, create_water_mask
from .model import OilSpillModel
from .visualization import plot_background, plot_spill, setup_axes


def _ensure_output_dirs(run_cfg: RunConfig) -> None:
    run_cfg.output_frames_dir.mkdir(parents=True, exist_ok=True)
    run_cfg.output_mass_dir.mkdir(parents=True, exist_ok=True)


def _resolve_source_index(
    source_lat_lon: Tuple[float, float],
    domain: DomainConfig,
) -> Tuple[int, int]:
    lat, lon = source_lat_lon
    lat_scale = (lat - domain.latitude_min) / (domain.latitude_max - domain.latitude_min)
    lon_scale = (lon - domain.longitude_min) / (domain.longitude_max - domain.longitude_min)
    i = int(min(max(lat_scale, 0.0), 1.0) * (domain.height - 1))
    j = int(min(max(lon_scale, 0.0), 1.0) * (domain.width - 1))
    return i, j


def run_simulation(
    source_lat_lon: Tuple[float, float] = (28.7, -88.3),
    initial_oil_mass: float = 100.0,
    temperature_c: float = 20.0,
    domain_cfg: Optional[DomainConfig] = None,
    model_cfg: Optional[ModelConfig] = None,
    run_cfg: Optional[RunConfig] = None,
    render: bool = True,
) -> OilSpillModel:
    domain_cfg = domain_cfg or DomainConfig()
    model_cfg = model_cfg or ModelConfig()
    run_cfg = run_cfg or RunConfig()

    _ensure_output_dirs(run_cfg)

    env = load_environmental_data(
        sea_csv_path=str(run_cfg.sea_currents_csv),
        wind_csv_path=str(run_cfg.wind_currents_csv),
        domain=domain_cfg,
    )

    dates = list(iter_dates(run_cfg.simulation_start, run_cfg.simulation_end))
    sea_currents = interpolate_vectors(env.sea_currents, domain_cfg.height, domain_cfg.width, dates)
    wind_currents = interpolate_vectors(env.wind_currents, domain_cfg.height, domain_cfg.width, dates)

    land_mask = create_land_mask(domain_cfg)
    water = create_water_mask(domain_cfg, land_mask)

    oil = np.zeros((domain_cfg.height, domain_cfg.width), dtype=float)
    source_index = _resolve_source_index(source_lat_lon, domain_cfg)
    oil[source_index] = initial_oil_mass

    model = OilSpillModel(
        water=water,
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
    )

    fig = ax = None
    if render:
        fig, ax = setup_axes(domain_cfg)

    step = 0
    for date in dates:
        for _ in range(run_cfg.steps_per_day):
            model.step(date)

            if render and ax is not None:
                ax.clear()
                plot_background(
                    ax=ax,
                    domain=domain_cfg,
                    map_image_path=Path(run_cfg.map_image_path),
                    sea_points=env.sea_points,
                    wind_points=env.wind_points,
                )
                plot_spill(ax, domain_cfg, model.oil_mass, title=f"step={step} mass={model.total_mass:.2f}")
                plt.pause(run_cfg.plot_pause_seconds)
                fig.savefig(run_cfg.output_frames_dir / f"oil_spill_{step}.png", dpi=120)

            with open(run_cfg.output_mass_dir / f"step_{step}.json", "w", encoding="utf-8") as file:
                json.dump(model.oil_mass.tolist(), file)

            step += 1

    if render:
        plt.show()

    return model
