from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DomainConfig:
    latitude_min: float = 25.5
    latitude_max: float = 31.0
    longitude_min: float = -98.5
    longitude_max: float = -87.5
    height: int = 100
    width: int = 200


@dataclass(frozen=True)
class ModelConfig:
    alpha: float = 1.0
    beta: float = 0.2
    movement_diffusion_coefficient: float = 0.03
    diagonal_diffusion_coefficient: float = 0.015
    round_precision: int = 4
    initial_spill_days: int = 12


@dataclass(frozen=True)
class RunConfig:
    data_dir: Path = Path("data")
    output_frames_dir: Path = Path("oil_spill_output")
    output_mass_dir: Path = Path("oil_mass_data")
    map_image_path: Path = Path("data/map3.jpg")
    sea_currents_csv: Path = Path("data/filtered_sea_current_data.csv")
    wind_currents_csv: Path = Path("data/filtered_wind_data.csv")
    simulation_start: str = "2010-12-01"
    simulation_end: str = "2010-12-21"
    steps_per_day: int = 8
    save_every_step: bool = True
    plot_pause_seconds: float = 0.01
