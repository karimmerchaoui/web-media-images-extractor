"""
Image loading, quality-gating, and persistence helpers.

Kept dependency-light (Pillow + requests only) and free of Selenium/OpenCV
so this module can be imported and unit tested without a browser or video
stack available.
"""

import os
import uuid
from io import BytesIO
from typing import Optional, Union

import requests
from PIL import Image

from .config import DEFAULT_MIN_RESOLUTION, JPEG_QUALITY


def load_image(image_data: Union[bytes, str], timeout: int = 10) -> Optional[Image.Image]:
    """
    Load a PIL Image from raw bytes or a URL.

    Args:
        image_data: Raw image bytes, or a URL string to download from.
        timeout: Request timeout in seconds, used only for URL input.

    Returns:
        A PIL Image, or None if the input type is unsupported or loading failed.
    """
    try:
        if isinstance(image_data, bytes):
            return Image.open(BytesIO(image_data))
        if isinstance(image_data, str):
            response = requests.get(image_data, timeout=timeout)
            response.raise_for_status()
            return Image.open(BytesIO(response.content))
        return None
    except Exception:
        return None


def image_passes_resolution_gate(
    img: Image.Image, min_resolution: int = DEFAULT_MIN_RESOLUTION
) -> bool:
    """
    Check whether an image meets the minimum width/height quality threshold.

    Images below this threshold are discarded rather than upscaled, since
    upscaling would manufacture fake detail rather than fix the underlying
    quality issue.
    """
    return img.width >= min_resolution and img.height >= min_resolution


def save_image(
    img: Image.Image,
    output_dir: str,
    prefix: str = "image",
    quality: int = JPEG_QUALITY,
) -> str:
    """
    Save a PIL Image to disk as a JPEG with a unique, collision-free filename.

    Returns:
        The path the image was saved to.
    """
    filename = f"{prefix}_{uuid.uuid4().hex[:8]}.jpg"
    filepath = os.path.join(output_dir, filename)
    img.convert("RGB").save(filepath, "JPEG", quality=quality)
    return filepath


def load_and_save_if_valid(
    image_data: Union[bytes, str],
    output_dir: str,
    prefix: str = "image",
    min_resolution: int = DEFAULT_MIN_RESOLUTION,
) -> Optional[str]:
    """
    Load an image, apply the resolution gate, and save it if it passes.

    Returns:
        The saved file path, or None if the image was invalid or too small.
    """
    img = load_image(image_data)
    if img is None:
        return None
    if not image_passes_resolution_gate(img, min_resolution):
        return None
    return save_image(img, output_dir, prefix)
