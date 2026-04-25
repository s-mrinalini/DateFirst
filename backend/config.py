"""
Shared configuration. Single source of truth for secrets & legal versions
so server.py and websocket_handler.py can't drift.
"""
import os
import secrets
import logging

logger = logging.getLogger(__name__)

ENV = os.environ.get("ENV", "development").lower()
APP_URL = os.environ.get("APP_URL", "http://localhost:3000").rstrip("/")

_WEAK_DEFAULTS = {
    "",
    "datefirst-secret-key-change-in-production",
    "changeme",
    "secret",
}


def _resolve_jwt_secret() -> str:
    raw = os.environ.get("JWT_SECRET", "")
    if raw in _WEAK_DEFAULTS or len(raw) < 32:
        if ENV == "production":
            raise RuntimeError(
                "JWT_SECRET is missing or weak. Set a 32+ char random secret. "
                'Generate: python -c "import secrets; print(secrets.token_urlsafe(48))"'
            )
        logger.warning(
            "JWT_SECRET is weak — DEV ONLY. Do NOT deploy this way. "
            "Set JWT_SECRET to a 32+ char value before production."
        )
        if not raw:
            raw = "dev-only-insecure-" + secrets.token_urlsafe(32)
    return raw


JWT_SECRET = _resolve_jwt_secret()
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24 * 7

LEGAL_TERMS_VERSION = "2026-04-25"
LEGAL_PRIVACY_VERSION = "2026-04-25"

ALLOWED_IMAGE_MIMES = {"image/jpeg", "image/png", "image/webp"}
MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB
MAX_IMAGE_DIMENSION = 2048  # cap to avoid PNG bombs
