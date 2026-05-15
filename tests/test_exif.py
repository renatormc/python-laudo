from pathlib import Path

import piexif  # type: ignore[import-untyped]
from PIL import Image

from laudo.exif import clear_caption, get_caption, has_caption, set_caption


def test_roundtrip_caption(tmp_path: Path):
    path = tmp_path / "test.jpg"
    img = Image.new("RGB", (10, 10))
    img.save(str(path))

    assert get_caption(path) == ""
    assert not has_caption(path)

    set_caption(path, "My caption")
    assert get_caption(path) == "My caption"
    assert has_caption(path)

    clear_caption(path)
    assert get_caption(path) == ""
    assert not has_caption(path)


def test_set_caption_updates_in_place(tmp_path: Path):
    path = tmp_path / "test.jpg"
    img = Image.new("RGB", (10, 10))
    img.save(str(path))

    set_caption(path, "First")
    assert get_caption(path) == "First"

    set_caption(path, "Updated")
    assert get_caption(path) == "Updated"


def test_get_caption_missing_file(tmp_path: Path):
    assert get_caption(tmp_path / "nonexistent.jpg") == ""


def test_has_caption(tmp_path: Path):
    path = tmp_path / "test.jpg"
    img = Image.new("RGB", (10, 10))
    img.save(str(path))

    assert not has_caption(path)
    set_caption(path, "Hello")
    assert has_caption(path)


def test_accented_characters(tmp_path: Path):
    path = tmp_path / "test.jpg"
    img = Image.new("RGB", (10, 10))
    img.save(str(path))

    caption = "Coração à moda do Porto — é uma maravilha!"
    set_caption(path, caption)
    assert get_caption(path) == caption


def test_set_caption_with_existing_exif_components(tmp_path: Path):
    """Reproduce piexif dump crash on ComponentsConfiguration tuple."""
    path = tmp_path / "test.jpg"
    Image.new("RGB", (10, 10)).save(str(path))

    exif_dict = piexif.load(str(path))
    exif_dict["Exif"][piexif.ExifIFD.ComponentsConfiguration] = b"\x01\x02\x03\x00"
    exif_bytes = piexif.dump(exif_dict)
    with Image.open(path) as img:
        img.save(str(path), exif=exif_bytes)

    set_caption(path, "works with components config")
    assert get_caption(path) == "works with components config"


def test_set_caption_with_large_rational_tags(tmp_path: Path):
    """Large rational values (>255) must not be blindly converted to bytes."""
    path = tmp_path / "test.jpg"
    Image.new("RGB", (10, 10)).save(str(path))

    exif_dict = piexif.load(str(path))
    exif_dict["Exif"][piexif.ExifIFD.FocalLength] = (12345, 1000)
    exif_bytes = piexif.dump(exif_dict)
    with Image.open(path) as img:
        img.save(str(path), exif=exif_bytes)

    set_caption(path, "works with large rationals")
    assert get_caption(path) == "works with large rationals"
