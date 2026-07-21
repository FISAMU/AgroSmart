# ══════════════════════════════════════════════════════
#  config.py — Configuration AgroSmart (.env)
# ══════════════════════════════════════════════════════

import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent / ".env")
except ImportError:
    pass

def _env(name: str, default: str = "") -> str:
    value = os.getenv(name, default)
    if not value:
        return default
    return value.strip().strip('"').strip("'")


EMAIL_ADDRESS = _env("EMAIL_ADDRESS")
EMAIL_PASSWORD = _env("EMAIL_PASSWORD").replace(" ", "")

SMTP_SERVER = _env("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(_env("SMTP_PORT", "587") or "587")

CODE_EXPIRY_MINUTES = 10

DATABASE_URL = os.getenv("DATABASE_URL", "")
