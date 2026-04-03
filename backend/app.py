from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from backend.db import create_user, initialize_database, list_recent_runs, save_simulation_run, verify_user
from backend.schemas import AuthRequest, SimulationRequest
from backend.simulation_service import run_preview_simulation

app = FastAPI(title="Contamination Predictor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MAP_BACKGROUND_PATH = Path(__file__).resolve().parent.parent / "data" / "map3.jpg"


@app.on_event("startup")
def on_startup() -> None:
    initialize_database()


@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/map-background")
def map_background() -> FileResponse:
    if not MAP_BACKGROUND_PATH.exists():
        raise HTTPException(status_code=404, detail="Mapa nie została znaleziona")

    return FileResponse(MAP_BACKGROUND_PATH)


@app.post("/api/auth/register")
def register(payload: AuthRequest) -> dict[str, object]:
    user = create_user(payload.username, payload.password)
    if user is None:
        raise HTTPException(status_code=409, detail="Uzytkownik juz istnieje")
    return {"id": user["id"], "username": user["username"], "createdAt": user["created_at"]}


@app.post("/api/auth/login")
def login(payload: AuthRequest) -> dict[str, object]:
    user = verify_user(payload.username, payload.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Nieprawidlowy login lub haslo")
    return user


@app.get("/api/users/{username}/runs")
def get_runs(username: str) -> list[dict[str, object]]:
    return list_recent_runs(username)


@app.post("/api/simulations/run")
def run_simulation(payload: SimulationRequest) -> dict[str, object]:
    result = run_preview_simulation(
        source_lat=payload.source_lat,
        source_lon=payload.source_lon,
        initial_oil_mass=payload.initial_oil_mass,
        temperature_c=payload.temperature_c,
        days=payload.days,
        steps_per_day=payload.steps_per_day,
    )
    run_record = save_simulation_run(payload.username, result)
    return {"run": run_record, "result": result}
