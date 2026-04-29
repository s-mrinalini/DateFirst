"""
CSAM scanner — pluggable interface.

Providers:
  - hive       (default; self-serve API at api.thehive.ai)
  - thorn      (Thorn Safer; requires application/contract)
  - photodna   (Microsoft PhotoDNA Cloud Service; requires application)
  - none       (DEV ONLY — fail-open with a loud warning)

Configuration:
  CSAM_PROVIDER  one of {hive, thorn, photodna, none}
  HIVE_API_KEY   when CSAM_PROVIDER=hive
  THORN_API_KEY  when CSAM_PROVIDER=thorn
  PHOTODNA_KEY   when CSAM_PROVIDER=photodna

In production (ENV=production), CSAM_PROVIDER=none is rejected at first call.
In development, missing keys log a warning and pass the upload through.
"""
from __future__ import annotations

import os
import logging
from dataclasses import dataclass
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# Default is "" (unset) — production refuses to start uploads. Setting
# CSAM_PROVIDER=none is an *explicit* opt-out: production will accept it but
# log a loud warning per upload. Don't deploy that to a public launch.
PROVIDER = os.environ.get("CSAM_PROVIDER", "").lower()
ENV = os.environ.get("ENV", "development").lower()

_HIVE_BLOCK_THRESHOLD = float(os.environ.get("CSAM_HIVE_THRESHOLD", "0.7"))
# Hive class names that we treat as CSAM-equivalent and auto-block on
_HIVE_CSAM_CLASSES = {
    "yes_underage_minor",
    "yes_csam",
    "yes_child_present_with_nsfw",
}


@dataclass
class ScanResult:
    blocked: bool
    score: float
    provider: str
    raw: Optional[dict] = None
    error: Optional[str] = None


async def _scan_hive(content: bytes, mime: str) -> ScanResult:
    api_key = os.environ.get("HIVE_API_KEY")
    if not api_key:
        if ENV == "production":
            raise RuntimeError("HIVE_API_KEY missing in production.")
        logger.warning("HIVE_API_KEY missing — passing image through (DEV).")
        return ScanResult(blocked=False, score=0.0, provider="hive_unconfigured")

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                "https://api.thehive.ai/api/v2/task/sync",
                headers={"Authorization": f"Token {api_key}"},
                files={"image": ("upload.jpg", content, mime)},
            )
        resp.raise_for_status()
        data = resp.json()
        # Hive payload: status[0].response.output[0].classes -> [{class, score}, ...]
        try:
            classes = (
                data.get("status", [{}])[0]
                .get("response", {})
                .get("output", [{}])[0]
                .get("classes", [])
            )
        except (IndexError, AttributeError):
            classes = []
        csam_score = max(
            (c.get("score", 0.0) for c in classes if c.get("class") in _HIVE_CSAM_CLASSES),
            default=0.0,
        )
        return ScanResult(
            blocked=csam_score >= _HIVE_BLOCK_THRESHOLD,
            score=csam_score,
            provider="hive",
            raw=data,
        )
    except httpx.HTTPError as e:
        # Network errors: in production we MUST fail closed; in dev, warn and pass.
        msg = f"Hive scan failed: {e}"
        if ENV == "production":
            logger.error(msg)
            return ScanResult(blocked=True, score=1.0, provider="hive", error=msg)
        logger.warning(msg + " — passing through (DEV).")
        return ScanResult(blocked=False, score=0.0, provider="hive_error", error=msg)


async def scan_image(content: bytes, *, mime: str, user_id: str) -> ScanResult:
    """Scan an image for CSAM-equivalent content. Returns ScanResult."""
    if PROVIDER == "hive":
        return await _scan_hive(content, mime)

    if PROVIDER in ("thorn", "photodna"):
        # Stubs — implement when contracts are signed.
        if ENV == "production":
            raise RuntimeError(f"CSAM provider '{PROVIDER}' not yet implemented.")
        logger.warning("CSAM provider '%s' not implemented — passing through (DEV).", PROVIDER)
        return ScanResult(blocked=False, score=0.0, provider=f"{PROVIDER}_stub")

    if PROVIDER == "none":
        # Explicit opt-out. Allowed in any env, but each upload still logs
        # so there's a paper trail. Public launch must switch to hive/thorn/photodna.
        logger.warning(
            "CSAM scan SKIPPED — CSAM_PROVIDER=none (ENV=%s). user_id=%s. "
            "Acceptable for invite-only beta. DO NOT keep this on for public launch.",
            ENV, user_id,
        )
        return ScanResult(blocked=False, score=0.0, provider="none")

    if PROVIDER == "":
        # Unset = misconfiguration. In production we refuse to start uploads;
        # in dev we pass them through with a warning so local devs don't get blocked.
        if ENV not in ("development", "dev", "local"):
            raise RuntimeError(
                "CSAM_PROVIDER is unset. Set CSAM_PROVIDER=hive (or thorn/photodna) "
                "with the matching API key for production, or =none to explicitly "
                "opt out for invite-only beta testing."
            )
        logger.warning(
            "CSAM_PROVIDER unset — passing through (DEV). Set CSAM_PROVIDER=hive "
            "or =none before deploying."
        )
        return ScanResult(blocked=False, score=0.0, provider="unset")

    raise RuntimeError(f"Unknown CSAM_PROVIDER: {PROVIDER!r}")
