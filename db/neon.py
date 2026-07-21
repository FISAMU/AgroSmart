"""
Couche d'accès PostgreSQL (Neon) pour AgroSmart.
Configure DATABASE_URL dans .env ou les variables d'environnement.
"""
import json
import os
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Optional

import psycopg2
from psycopg2.extras import Json, RealDictCursor, execute_values

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from config import DATABASE_URL

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY,
    nom VARCHAR(100),
    prenom VARCHAR(100),
    sexe VARCHAR(20),
    tel VARCHAR(50),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS password_reset_codes (
    email VARCHAR(255) PRIMARY KEY,
    code VARCHAR(6) NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS cultures_ref (
    nom VARCHAR(100) PRIMARY KEY,
    ph_min DOUBLE PRECISION NOT NULL,
    ph_max DOUBLE PRECISION NOT NULL,
    hum_min DOUBLE PRECISION NOT NULL,
    besoin_eau_base DOUBLE PRECISION NOT NULL,
    hum_optimal DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS donnees_capteurs (
    id BIGSERIAL PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    data JSONB NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_donnees_capteurs_user_ts
    ON donnees_capteurs (user_id, timestamp DESC);

CREATE TABLE IF NOT EXISTS app_config (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
"""


def _require_database_url() -> str:
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL manquant. Créez un projet sur https://neon.tech, "
            "copiez la connection string dans .env (voir .env.example)."
        )
    return DATABASE_URL


@contextmanager
def get_connection():
    conn = psycopg2.connect(_require_database_url())
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def ensure_schema() -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(SCHEMA_SQL)
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash TEXT;")


def get_user_by_email(email: str) -> Optional[dict[str, Any]]:
    email_norm = email.strip().lower()
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM users WHERE LOWER(email) = %s", (email_norm,))
            row = cur.fetchone()
            return dict(row) if row else None


def create_user(
    user_id: str,
    nom: str,
    prenom: str,
    sexe: str,
    tel: str,
    email: str,
    password_hash: str = "",
) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (id, nom, prenom, sexe, tel, email, password_hash)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    nom = EXCLUDED.nom,
                    prenom = EXCLUDED.prenom,
                    sexe = EXCLUDED.sexe,
                    tel = EXCLUDED.tel,
                    email = EXCLUDED.email,
                    password_hash = EXCLUDED.password_hash
                """,
                (user_id, nom, prenom, sexe, tel, email.strip().lower(), password_hash),
            )


def get_user(user_id: str) -> Optional[dict[str, Any]]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            row = cur.fetchone()
            return dict(row) if row else None


def list_culture_names() -> list[str]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT nom FROM cultures_ref ORDER BY nom")
            return [row[0] for row in cur.fetchall()]


def get_culture(nom: str) -> Optional[dict[str, Any]]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM cultures_ref WHERE nom = %s", (nom,))
            row = cur.fetchone()
            return dict(row) if row else None


def upsert_culture(
    nom: str,
    ph_min: float,
    ph_max: float,
    hum_min: float,
    besoin_eau_base: float,
    hum_optimal: Optional[float] = None,
) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO cultures_ref (nom, ph_min, ph_max, hum_min, besoin_eau_base, hum_optimal)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (nom) DO UPDATE SET
                    ph_min = EXCLUDED.ph_min,
                    ph_max = EXCLUDED.ph_max,
                    hum_min = EXCLUDED.hum_min,
                    besoin_eau_base = EXCLUDED.besoin_eau_base,
                    hum_optimal = EXCLUDED.hum_optimal
                """,
                (nom, ph_min, ph_max, hum_min, besoin_eau_base, hum_optimal),
            )


def bulk_upsert_cultures(rows: list[tuple]) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            execute_values(
                cur,
                """
                INSERT INTO cultures_ref (nom, ph_min, ph_max, hum_min, besoin_eau_base)
                VALUES %s
                ON CONFLICT (nom) DO UPDATE SET
                    ph_min = EXCLUDED.ph_min,
                    ph_max = EXCLUDED.ph_max,
                    hum_min = EXCLUDED.hum_min,
                    besoin_eau_base = EXCLUDED.besoin_eau_base
                """,
                rows,
            )


def insert_sensor_reading(user_id: str, data: dict[str, Any]) -> None:
    payload = dict(data)
    ts = payload.pop("timestamp", None)
    if isinstance(ts, datetime):
        timestamp = ts
    else:
        timestamp = datetime.now()

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO donnees_capteurs (user_id, timestamp, data)
                VALUES (%s, %s, %s)
                """,
                (user_id, timestamp, Json(payload, dumps=_json_dumps)),
            )


def get_sensor_readings(user_id: str, limit: int = 30) -> list[dict[str, Any]]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT timestamp, data
                FROM donnees_capteurs
                WHERE user_id = %s
                ORDER BY timestamp DESC
                LIMIT %s
                """,
                (user_id, limit),
            )
            rows = cur.fetchall()

    results: list[dict[str, Any]] = []
    for row in reversed(rows):
        item = dict(row["data"])
        item["timestamp"] = row["timestamp"]
        results.append(item)
    return results


def set_config(key: str, value: str) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO app_config (key, value, updated_at)
                VALUES (%s, %s, NOW())
                ON CONFLICT (key) DO UPDATE SET
                    value = EXCLUDED.value,
                    updated_at = NOW()
                """,
                (key, value),
            )


def get_config(key: str) -> Optional[str]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT value FROM app_config WHERE key = %s", (key,))
            row = cur.fetchone()
            return row[0] if row else None


def _json_dumps(obj: Any) -> str:
    return json.dumps(obj, default=str)
