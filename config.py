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

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

CODE_EXPIRY_MINUTES = 10

DATABASE_URL = os.getenv("DATABASE_URL", "")
