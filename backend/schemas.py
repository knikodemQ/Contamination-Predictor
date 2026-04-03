from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class AuthRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=4, max_length=64)


class SimulationRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    username: str = Field(min_length=3, max_length=32)
    source_lat: float = Field(alias="sourceLat")
    source_lon: float = Field(alias="sourceLon")
    initial_oil_mass: float = Field(alias="initialOilMass", ge=1.0)
    temperature_c: float = Field(alias="temperatureC", ge=-10.0, le=60.0)
    days: int = Field(default=4, ge=1, le=10)
    steps_per_day: int = Field(default=3, alias="stepsPerDay", ge=1, le=12)
