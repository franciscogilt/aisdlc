"""Configuracion minima del proyecto. Todo lo sensible viene del entorno (ver .env.example)."""
import os
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

APP_ENV = os.environ.get("APP_ENV", "production")
DEBUG = APP_ENV == "development"
TESTING = sys.argv[1:2] == ["test"]

# La clave de desarrollo solo se acepta en desarrollo o al correr tests; en cualquier otro caso es obligatoria.
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY") or ("dev-insecure-key-change-me" if DEBUG or TESTING else None)
if not SECRET_KEY:
    raise ImproperlyConfigured("Define DJANGO_SECRET_KEY en el entorno.")

ALLOWED_HOSTS = [h.strip() for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,[::1]").split(",")]

INSTALLED_APPS = ["core"]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

# Con DATABASE_URL (postgresql://usuario:clave@host:5432/base) usa PostgreSQL; sin ella, SQLite para arrancar sin servicios.
_db_url = os.environ.get("DATABASE_URL")
if _db_url:
    _u = urlparse(_db_url)
    DATABASES = {"default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": _u.path.lstrip("/"),
        "USER": unquote(_u.username or ""),
        "PASSWORD": unquote(_u.password or ""),
        "HOST": _u.hostname or "",
        "PORT": _u.port or "",
    }}
else:
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
