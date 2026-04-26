"""
Shared configuration. Single source of truth for secrets & legal versions
so server.py and websocket_handler.py can't drift.
"""
import os
import secrets
import logging

logger = logging.getLogger(__name__)

# ENV is left unset deliberately so deployments without an explicit ENV value
# get treated as production for safety checks (fail-fast on weak secrets).
# Local devs should set ENV=development in .env to opt in to the dev fallback.
ENV = os.environ.get("ENV", "").lower()
APP_URL = os.environ.get("APP_URL", "http://localhost:3000").rstrip("/")

_DEV_ENVS = {"development", "dev", "local"}
_WEAK_DEFAULTS = {
    "",
    "datefirst-secret-key-change-in-production",
    "changeme",
    "secret",
}


def is_dev() -> bool:
    return ENV in _DEV_ENVS


def _resolve_jwt_secret() -> str:
    raw = os.environ.get("JWT_SECRET", "")
    is_weak = raw in _WEAK_DEFAULTS or len(raw) < 32

    if is_weak and not is_dev():
        # Anything that's not an explicit dev env (production, staging, test,
        # or ENV unset) must have a real secret. Refuse to start.
        raise RuntimeError(
            "JWT_SECRET is missing or too short (need 32+ chars). "
            f"Current ENV={ENV!r}. Refusing to start.\n"
            "Generate a secret:\n"
            '  python -c "import secrets; print(secrets.token_urlsafe(48))"\n'
            "Then set JWT_SECRET in your deployment environment "
            "(e.g. Render → Service → Environment).\n"
            "For local development, also set ENV=development in your .env."
        )

    if is_weak:
        logger.warning(
            "JWT_SECRET is weak — DEV ONLY (ENV=%s). Do NOT deploy this way.",
            ENV,
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
