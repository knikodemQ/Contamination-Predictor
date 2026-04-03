from __future__ import annotations

import hashlib
import json
import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "app_data"
DB_PATH = DATA_DIR / "contamination_demo.sqlite3"


def _connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database() -> None:
    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                salt TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS simulation_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                created_at TEXT NOT NULL,
                source_lat REAL NOT NULL,
                source_lon REAL NOT NULL,
                initial_oil_mass REAL NOT NULL,
                temperature_c REAL NOT NULL,
                steps INTEGER NOT NULL,
                total_mass REAL NOT NULL,
                max_cell_mass REAL NOT NULL,
                snapshots_json TEXT NOT NULL,
                final_grid_json TEXT NOT NULL
            )
            """
        )
        connection.commit()


def _hash_password(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120_000).hex()


def create_user(username: str, password: str) -> dict[str, Any] | None:
    salt = secrets.token_hex(16)
    created_at = datetime.now(timezone.utc).isoformat()
    password_hash = _hash_password(password, salt)

    try:
        with _connect() as connection:
            cursor = connection.execute(
                "INSERT INTO users (username, salt, password_hash, created_at) VALUES (?, ?, ?, ?)",
                (username, salt, password_hash, created_at),
            )
            connection.commit()
    except sqlite3.IntegrityError:
        return None

    return get_user_by_username(username)


def get_user_by_username(username: str) -> dict[str, Any] | None:
    with _connect() as connection:
        row = connection.execute(
            "SELECT id, username, salt, password_hash, created_at FROM users WHERE username = ?",
            (username,),
        ).fetchone()

    if row is None:
        return None

    return dict(row)


def verify_user(username: str, password: str) -> dict[str, Any] | None:
    user = get_user_by_username(username)
    if user is None:
        return None

    expected_hash = _hash_password(password, user["salt"])
    if expected_hash != user["password_hash"]:
        return None

    return {"id": user["id"], "username": user["username"], "created_at": user["created_at"]}


def save_simulation_run(username: str, payload: dict[str, Any]) -> dict[str, Any]:
    created_at = datetime.now(timezone.utc).isoformat()
    with _connect() as connection:
        cursor = connection.execute(
            """
            INSERT INTO simulation_runs (
                username,
                created_at,
                source_lat,
                source_lon,
                initial_oil_mass,
                temperature_c,
                steps,
                total_mass,
                max_cell_mass,
                snapshots_json,
                final_grid_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                username,
                created_at,
                payload["source_lat"],
                payload["source_lon"],
                payload["initial_oil_mass"],
                payload["temperature_c"],
                payload["steps"],
                payload["total_mass"],
                payload["max_cell_mass"],
                json.dumps(payload["snapshots"]),
                json.dumps(payload["final_grid"]),
            ),
        )
        run_id = cursor.lastrowid
        connection.commit()

    return {
        "id": run_id,
        "username": username,
        "created_at": created_at,
    }


def list_recent_runs(username: str, limit: int = 5) -> list[dict[str, Any]]:
    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT id, created_at, source_lat, source_lon, initial_oil_mass, temperature_c, steps, total_mass, max_cell_mass
            FROM simulation_runs
            WHERE username = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (username, limit),
        ).fetchall()

    return [dict(row) for row in rows]
