"""
Image validation + normalization for user uploads.

Steps:
1. Magic-byte sniff via python-magic (defends against extension spoofing).
2. Pillow `verify()` to reject malformed images.
3. Re-open and re-encode to JPEG, stripping EXIF/GPS metadata.
4. Cap dimensions to defend against decompression bombs.
"""
from __future__ import annotations

import io
import logging
from typing import Iterable

from PIL import Image, ImageOps

try:
    import magic  # python-magic
    _HAS_MAGIC = True
except (ImportError, OSError):
    # python-magic needs libmagic on the host; fall back to Pillow-only sniffing
    # if libmagic isn't installed (still safer than naive content_type trust).
    _HAS_MAGIC = False

logger = logging.getLogger(__name__)

# Pillow's bomb protection — explicit, not env-dependent
Image.MAX_IMAGE_PIXELS = 50_000_000  # 50 MP


def _sniff_mime(buf: bytes) -> str:
    if _HAS_MAGIC:
        return magic.from_buffer(buf, mime=True)
    # Fallback: trust Pillow's format detection
    try:
        with Image.open(io.BytesIO(buf)) as im:
            fmt = (im.format or "").lower()
            return {
                "jpeg": "image/jpeg",
                "jpg": "image/jpeg",
                "png": "image/png",
                "webp": "image/webp",
            }.get(fmt, "application/octet-stream")
    except Exception:
        return "application/octet-stream"


def validate_and_normalize_image(
    raw: bytes,
    *,
    allowed_mimes: Iterable[str],
    max_dim: int = 2048,
    quality: int = 85,
) -> tuple[bytes, str, tuple[int, int]]:
    """
    Validate an uploaded image and return normalized JPEG bytes.

    Returns: (normalized_bytes, output_mime, (width, height))
    Raises: ValueError on any validation failure.
    """
    if not raw:
        raise ValueError("Empty file.")

    sniffed = _sniff_mime(raw)
    if sniffed not in allowed_mimes:
        raise ValueError(f"Unsupported image type: {sniffed}. Allowed: JPEG, PNG, WebP.")

    # Pillow verify (must re-open after verify per PIL docs)
    try:
        with Image.open(io.BytesIO(raw)) as probe:
            probe.verify()
    except Exception as e:
        raise ValueError(f"Image failed validation: {e}")

    try:
        with Image.open(io.BytesIO(raw)) as im:
            # Honor EXIF orientation, then strip everything else
            im = ImageOps.exif_transpose(im)
            if im.mode not in ("RGB", "L"):
                im = im.convert("RGB")
            # Cap dimensions
            im.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
            out = io.BytesIO()
            # JPEG with no EXIF, no ICC profile preserved
            im.save(out, format="JPEG", quality=quality, optimize=True)
            data = out.getvalue()
            return data, "image/jpeg", im.size
    except Exception as e:
        raise ValueError(f"Could not process image: {e}")
