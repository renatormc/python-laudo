"""Image listing, thumbnails and reduced copies for a project's ``fotos/`` folder.

Every function takes an optional ``folder`` (the project folder). When omitted,
the current working directory is used, which keeps the old call style working.
Passing ``folder`` explicitly is preferred: it avoids ``os.chdir`` and is safe
to call from background threads.
"""
from pathlib import Path

from PIL import Image, ImageOps

from . import db

_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".webp"}
_THUMB_MAX = 300
_REDUCED_MAX = 450
_JPEG_MODES = {"RGB", "L", "CMYK"}


def _root(folder: Path | None) -> Path:
    return folder if folder is not None else Path.cwd()


def _fotos_dir(folder: Path | None = None) -> Path:
    return _root(folder) / "fotos"


def _thumbs_dir(folder: Path | None = None) -> Path:
    return _root(folder) / ".laudo" / "thumbs"


def _is_image(path: Path) -> bool:
    return path.suffix.lower() in _IMAGE_EXTENSIONS and path.is_file()


def _is_fresh(cached: Path, source: Path) -> bool:
    """True when ``cached`` exists and is not older than ``source``."""
    try:
        return cached.stat().st_mtime >= source.stat().st_mtime
    except FileNotFoundError:
        return False


def _save_resized(img: Image.Image, dest: Path, max_size: int) -> None:
    # For JPEGs, decode directly at a reduced scale (1/2, 1/4, 1/8) that is still
    # >= max_size: much faster than decoding the full image and shrinking it.
    img.draft(img.mode, (max_size, max_size))
    img = ImageOps.exif_transpose(img) or img
    img.thumbnail((max_size, max_size))
    if img.mode not in _JPEG_MODES:
        img = img.convert("RGB")
    dest.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(dest), "JPEG", quality=90)


def list_images(folder: Path | None = None) -> list[Path]:
    fotos = _fotos_dir(folder)
    if not fotos.is_dir():
        return []
    return sorted(p for p in fotos.rglob("*") if _is_image(p))


def get_image_path(name: str, folder: Path | None = None) -> Path | None:
    fotos = _fotos_dir(folder)
    if not fotos.is_dir():
        return None
    # One directory walk instead of one rglob per extension (and per case).
    return next((p for p in fotos.rglob(f"{name}.*") if p.stem == name and _is_image(p)), None)


def thumbnail_for(original: Path, folder: Path | None = None, *, source: Path | None = None) -> Path:
    """Thumbnail of ``original``; ``source`` may be a smaller copy to resize from."""
    thumb = _thumbs_dir(folder) / f"{original.stem}_thumb.jpg"
    src = source or original
    if not _is_fresh(thumb, src):
        with Image.open(src) as img:
            _save_resized(img, thumb, _THUMB_MAX)
    return thumb


def reduced_for(original: Path, folder: Path | None = None) -> Path:
    """Copy of ``original`` limited to ``_REDUCED_MAX`` px, or ``original`` if already small."""
    reduced = _thumbs_dir(folder) / f"{original.stem}_reduced.jpg"
    if _is_fresh(reduced, original):
        return reduced
    with Image.open(original) as img:  # only the header is read until resizing
        if max(img.size) <= _REDUCED_MAX:
            return original
        _save_resized(img, reduced, _REDUCED_MAX)
    return reduced


def get_thumbnail(name: str, folder: Path | None = None) -> Path | None:
    original = get_image_path(name, folder)
    return None if original is None else thumbnail_for(original, folder)


def get_reduced(name: str, folder: Path | None = None) -> Path | None:
    original = get_image_path(name, folder)
    return None if original is None else reduced_for(original, folder)


def get_caption(name: str, folder: Path | None = None) -> str:
    return db.get_caption(name, folder)


def set_caption(name: str, caption: str, folder: Path | None = None) -> None:
    if get_image_path(name, folder) is None:
        raise FileNotFoundError(f"Image '{name}' not found in fotos/")
    db.set_caption(name, caption, folder)
