"""Чтение переменных окружения из файла .env (без сторонних библиотек)."""

import os
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent


def read_dotenv(filename=".env"):
    path = PROJECT_DIR / filename
    if not path.exists():
        return
    with path.open(encoding="utf-8") as handle:
        for entry in handle:
            entry = entry.strip()
            if not entry or entry.startswith("#") or "=" not in entry:
                continue
            name, _, raw = entry.partition("=")
            os.environ.setdefault(name.strip(), raw.strip().strip("'\""))


def get(name, fallback=None):
    return os.environ.get(name, fallback)


def flag(name, fallback=False):
    value = os.environ.get(name)
    if value is None:
        return fallback
    return value.strip().lower() in ("1", "true", "yes", "on")
