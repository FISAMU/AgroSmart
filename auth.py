"""Authentification AgroSmart via Neon PostgreSQL."""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt

from db.neon import ensure_schema, get_connection, get_user_by_email as _get_user_by_email


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def register_user(
    nom: str,
    prenom: str,
    sexe: str,
    tel: str,
    email: str,
    password: str,
) -> str:
    if len(password) < 6:
        raise ValueError("Le mot de passe doit contenir au moins 6 caractères.")

    ensure_schema()
    email_norm = email.strip().lower()
    if _get_user_by_email(email_norm):
        raise ValueError("Un compte existe déjà avec cet email.")

    user_id = str(uuid.uuid4())
    password_hash = hash_password(password)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (id, nom, prenom, sexe, tel, email, password_hash)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (user_id, nom, prenom, sexe, tel, email_norm, password_hash),
            )
    return user_id


def authenticate_user(email: str, password: str) -> Optional[str]:
    user = _get_user_by_email(email.strip().lower())
    if not user or not user.get("password_hash"):
        return None
    if not verify_password(password, user["password_hash"]):
        return None
    return user["id"]


def save_reset_code(email: str, code: str, expiry_minutes: int = 10) -> None:
    email_norm = email.strip().lower()
    expires_at = _utc_now() + timedelta(minutes=expiry_minutes)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO password_reset_codes (email, code, expires_at)
                VALUES (%s, %s, %s)
                ON CONFLICT (email) DO UPDATE SET
                    code = EXCLUDED.code,
                    expires_at = EXCLUDED.expires_at
                """,
                (email_norm, code, expires_at),
            )


def verify_reset_code(email: str, code: str) -> bool:
    email_norm = email.strip().lower()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT code, expires_at
                FROM password_reset_codes
                WHERE email = %s
                """,
                (email_norm,),
            )
            row = cur.fetchone()
            if not row:
                return False
            stored_code, expires_at = row
            return stored_code == code.strip() and _utc_now() < _as_utc(expires_at)


def update_user_password(email: str, new_password: str) -> bool:
    if len(new_password) < 6:
        raise ValueError("Le mot de passe doit contenir au moins 6 caractères.")

    email_norm = email.strip().lower()
    password_hash = hash_password(new_password)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE users
                SET password_hash = %s
                WHERE email = %s
                """,
                (password_hash, email_norm),
            )
            updated = cur.rowcount > 0
            if updated:
                cur.execute(
                    "DELETE FROM password_reset_codes WHERE email = %s",
                    (email_norm,),
                )
            return updated


def clear_reset_code(email: str) -> None:
    email_norm = email.strip().lower()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM password_reset_codes WHERE email = %s",
                (email_norm,),
            )
