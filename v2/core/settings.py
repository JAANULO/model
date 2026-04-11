"""Wspolna konfiguracja runtime dla lokalnego uruchomienia i serwera."""

import os


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


APP_ENV = os.getenv("APP_ENV", "").strip().lower()
if not APP_ENV:
    APP_ENV = "render" if _as_bool(os.getenv("RENDER")) else "local"

# AUTO: postgres gdy jest DATABASE_URL, inaczej sqlite.
DB_BACKEND = os.getenv("DB_BACKEND", "auto").strip().lower()
DATABASE_URL = os.getenv("DATABASE_URL")

if DB_BACKEND == "auto":
    DB_BACKEND = "postgres" if DATABASE_URL else "sqlite"
elif DB_BACKEND not in {"postgres", "sqlite"}:
    DB_BACKEND = "sqlite"

DB_CONNECT_TIMEOUT = int(os.getenv("DB_CONNECT_TIMEOUT", "5"))
DB_SSLMODE = os.getenv("DB_SSLMODE", "require")

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# W lokalnym dev wygodny token domyslny; na serwerze wymagaj jawnej zmiennej.
if APP_ENV == "local":
    ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "dev-token-zmien-mnie")
else:
    ADMIN_TOKEN = os.getenv("ADMIN_TOKEN") or "__ADMIN_DISABLED__"

FLASK_HOST = os.getenv("HOST", "0.0.0.0")
FLASK_PORT = int(os.getenv("PORT", "5000"))
FLASK_DEBUG = _as_bool(os.getenv("FLASK_DEBUG"), default=(APP_ENV == "local"))

