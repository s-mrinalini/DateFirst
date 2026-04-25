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

PROVIDER = os.environ.get("CSAM_PROVIDER", "none").lower()
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
        if ENV == "production":
            raise RuntimeError(
                "CSAM_PROVIDER=none is not allowed in production. "
                "Set CSAM_PROVIDER=hive (or thorn/photodna) and the matching API key."
            )
        logger.warning(
            "CSAM scan SKIPPED — CSAM_PROVIDER=none. user_id=%s. "
            "DEV ONLY. This MUST NOT ship to production.",
            user_id,
        )
        return ScanResult(blocked=False, score=0.0, provider="none")

    raise RuntimeError(f"Unknown CSAM_PROVIDER: {PROVIDER!r}")
