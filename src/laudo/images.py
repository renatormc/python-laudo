from pathlib import Path

from PIL import Image

from .db import get_caption as _get_caption
from .db import set_caption as _set_caption

_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".webp"}
_THUMB_MAX = 300
_REDUCED_MAX = 1920


def _fotos_dir() -> Path:
    return Path.cwd() / "fotos"


def _laudo_dir() -> Path:
    return Path.cwd() / ".laudo"


def _thumbs_dir() -> Path:
    return _laudo_dir() / "thumbs"


def _ensure_thumbs() -> Path:
    d = _thumbs_dir()
    d.mkdir(parents=True, exist_ok=True)
    return d


def _thumb_path(name: str) -> Path:
    return _thumbs_dir() / f"{name}_thumb.jpg"


def _reduced_path(name: str) -> Path:
    return _thumbs_dir() / f"{name}_reduced.jpg"


def _find_by_name(name: str) -> Path | None:
    fotos = _fotos_dir()
    for ext in _IMAGE_EXTENSIONS:
        candidate = fotos / f"{name}{ext}"
        if candidate.is_file():
            return candidate
        candidate = fotos / f"{name}{ext.upper()}"
        if candidate.is_file():
            return candidate
    return None


def list_images() -> list[Path]:
    fotos = _fotos_dir()
    if not fotos.is_dir():
        return []
    return sorted(
        p for p in fotos.iterdir()
        if p.is_file() and p.suffix.lower() in _IMAGE_EXTENSIONS
    )


def get_image_path(name: str) -> Path | None:
    return _find_by_name(name)


def get_thumbnail(name: str) -> Path | None:
    original = _find_by_name(name)
    if original is None:
        return None
    thumb = _thumb_path(name)
    if thumb.is_file():
        return thumb
    _ensure_thumbs()
    with Image.open(original) as img:
        img.thumbnail((_THUMB_MAX, _THUMB_MAX))
        if img.mode == "RGBA":
            img = img.convert("RGB")
        img.save(str(thumb), "JPEG")
    return thumb
    _ensure_thumbs()
    with Image.open(original) as img:
        img.thumbnail((_THUMB_MAX, _THUMB_MAX))
        img.save(str(thumb), "JPEG")
    return thumb


def get_reduced(name: str) -> Path | None:
    original = _find_by_name(name)
    if original is None:
        return None
    with Image.open(original) as img:
        width, height = img.size
        if max(width, height) <= _REDUCED_MAX:
            return original
    reduced = _reduced_path(name)
    if reduced.is_file():
        return reduced
    _ensure_thumbs()
    with Image.open(original) as img:
        img.thumbnail((_REDUCED_MAX, _REDUCED_MAX))
        if img.mode == "RGBA":
            img = img.convert("RGB")
        img.save(str(reduced), "JPEG")
    return reduced


def get_caption(name: str) -> str:
    return _get_caption(name)


def set_caption(name: str, caption: str) -> None:
    if _find_by_name(name) is None:
        raise FileNotFoundError(f"Image '{name}' not found in fotos/")
    _set_caption(name, caption)
