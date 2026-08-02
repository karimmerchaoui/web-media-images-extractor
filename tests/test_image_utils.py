import io
import os

from PIL import Image

from media_extractor.image_utils import (
    image_passes_resolution_gate,
    load_and_save_if_valid,
    load_image,
    save_image,
)


def _make_image(width: int, height: int) -> Image.Image:
    return Image.new("RGB", (width, height), color=(200, 50, 50))


def _image_bytes(width: int, height: int, fmt: str = "JPEG") -> bytes:
    buf = io.BytesIO()
    _make_image(width, height).save(buf, format=fmt)
    return buf.getvalue()


# --- resolution gate ---------------------------------------------------


def test_image_passes_gate_when_large_enough():
    img = _make_image(500, 500)
    assert image_passes_resolution_gate(img, min_resolution=400) is True


def test_image_fails_gate_when_width_too_small():
    img = _make_image(300, 500)
    assert image_passes_resolution_gate(img, min_resolution=400) is False


def test_image_fails_gate_when_height_too_small():
    img = _make_image(500, 300)
    assert image_passes_resolution_gate(img, min_resolution=400) is False


def test_image_passes_gate_at_exact_threshold():
    img = _make_image(400, 400)
    assert image_passes_resolution_gate(img, min_resolution=400) is True


# --- load_image ---------------------------------------------------------


def test_load_image_from_bytes():
    data = _image_bytes(100, 100)
    img = load_image(data)
    assert img is not None
    assert img.size == (100, 100)


def test_load_image_returns_none_for_unsupported_type():
    assert load_image(12345) is None  # type: ignore[arg-type]


def test_load_image_returns_none_for_corrupt_bytes():
    assert load_image(b"not an image") is None


# --- save_image -----------------------------------------------------------


def test_save_image_creates_jpeg_file(tmp_path):
    img = _make_image(500, 500)
    filepath = save_image(img, str(tmp_path), prefix="test")
    assert os.path.exists(filepath)
    assert filepath.endswith(".jpg")


def test_save_image_filenames_are_unique(tmp_path):
    img = _make_image(500, 500)
    path_a = save_image(img, str(tmp_path), prefix="dup")
    path_b = save_image(img, str(tmp_path), prefix="dup")
    assert path_a != path_b


# --- load_and_save_if_valid (integration of the two steps above) ----------


def test_load_and_save_if_valid_saves_large_image(tmp_path):
    data = _image_bytes(500, 500)
    filepath = load_and_save_if_valid(data, str(tmp_path), prefix="ok", min_resolution=400)
    assert filepath is not None
    assert os.path.exists(filepath)


def test_load_and_save_if_valid_rejects_small_image(tmp_path):
    data = _image_bytes(200, 200)
    filepath = load_and_save_if_valid(data, str(tmp_path), prefix="small", min_resolution=400)
    assert filepath is None
    # nothing should have been written for a rejected image
    assert os.listdir(tmp_path) == []


def test_load_and_save_if_valid_rejects_corrupt_data(tmp_path):
    filepath = load_and_save_if_valid(b"garbage", str(tmp_path), prefix="bad")
    assert filepath is None
