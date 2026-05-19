from pathlib import Path

import piexif  # type: ignore[import-untyped]
from PIL import Image


_IMAGE_DESC_TAG = piexif.ImageIFD.ImageDescription


def _sanitize(exif_dict: dict) -> dict:
    """Convert Undefined-type tuples back to bytes for piexif.dump."""
    for ifd_name in ("0th", "Exif", "GPS", "1st"):
        ifd = exif_dict.get(ifd_name, {})
        info = piexif.TAGS.get(ifd_name, {})
        for tag, value in ifd.items():
            if isinstance(value, tuple) and info.get(tag, {}).get("type") == 7:
                ifd[tag] = bytes(value)
    return exif_dict


def get_caption(path: Path) -> str:
    """Read caption from the EXIF ImageDescription tag."""
    try:
        exif_dict = piexif.load(str(path))
        raw = exif_dict.get("0th", {}).get(_IMAGE_DESC_TAG)
        if raw is None:
            return ""
        if isinstance(raw, bytes):
            return raw.decode("utf-8", errors="replace")
        return str(raw)
    except Exception:
        return ""


def set_caption(path: Path, caption: str) -> None:
    """Write caption to the EXIF ImageDescription tag (in-place)."""
    exif_dict = piexif.load(str(path))
    exif_dict["0th"][_IMAGE_DESC_TAG] = caption.encode("utf-8")
    exif_bytes = piexif.dump(_sanitize(exif_dict))
    _save_exif(path, exif_bytes)


def clear_caption(path: Path) -> None:
    """Remove the EXIF ImageDescription tag."""
    exif_dict = piexif.load(str(path))
    exif_dict["0th"].pop(_IMAGE_DESC_TAG, None)
    exif_bytes = piexif.dump(_sanitize(exif_dict))
    _save_exif(path, exif_bytes)


def has_caption(path: Path) -> bool:
    """Check if the image has a non-empty caption."""
    return bool(get_caption(path))


def _save_exif(path: Path, exif_bytes: bytes) -> None:
    with Image.open(path) as img:
        img.save(path, exif=exif_bytes)
