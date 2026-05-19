from pathlib import Path

from PIL import Image

from laudo.images import (
    get_caption,
    get_image_path,
    get_reduced,
    get_thumbnail,
    list_images,
    set_caption,
)


def _make_image(path: Path, size: tuple[int, int] = (100, 100)):
    img = Image.new("RGB", size)
    img.save(str(path))


def test_list_images(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    fotos = tmp_path / "fotos"
    fotos.mkdir()
    _make_image(fotos / "a.jpg")
    _make_image(fotos / "b.png")
    (fotos / "note.txt").write_text("skip")
    result = list_images()
    assert len(result) == 2
    assert result[0].name == "a.jpg"
    assert result[1].name == "b.png"


def test_list_images_no_fotos_dir(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert list_images() == []


def test_get_image_path_found(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    fotos = tmp_path / "fotos"
    fotos.mkdir()
    _make_image(fotos / "photo.jpg")
    result = get_image_path("photo")
    assert result == fotos / "photo.jpg"


def test_get_image_path_case_insensitive_extension(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    fotos = tmp_path / "fotos"
    fotos.mkdir()
    _make_image(fotos / "Photo.JPG")
    result = get_image_path("Photo")
    assert result == fotos / "Photo.JPG"


def test_get_image_path_missing(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "fotos").mkdir()
    assert get_image_path("nonexistent") is None


def test_get_thumbnail_generates(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    fotos = tmp_path / "fotos"
    fotos.mkdir()
    _make_image(fotos / "test.png", (800, 600))
    thumb = get_thumbnail("test")
    assert thumb is not None
    assert thumb.name == "test_thumb.jpg"
    assert thumb.is_file()
    with Image.open(thumb) as img:
        assert img.size[0] <= 300
        assert img.size[1] <= 300


def test_get_thumbnail_cached(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    fotos = tmp_path / "fotos"
    fotos.mkdir()
    _make_image(fotos / "test.jpg", (800, 600))
    thumb1 = get_thumbnail("test")
    thumb2 = get_thumbnail("test")
    assert thumb1 == thumb2


def test_get_thumbnail_missing(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "fotos").mkdir()
    assert get_thumbnail("nonexistent") is None


def test_get_reduced_small_image_returns_original(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    fotos = tmp_path / "fotos"
    fotos.mkdir()
    _make_image(fotos / "small.jpg", (800, 600))
    result = get_reduced("small")
    assert result == fotos / "small.jpg"


def test_get_reduced_large_image_resizes(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    fotos = tmp_path / "fotos"
    fotos.mkdir()
    _make_image(fotos / "large.jpg", (3000, 2000))
    result = get_reduced("large")
    assert result is not None
    assert result.name == "large_reduced.jpg"
    assert result.is_file()
    with Image.open(result) as img:
        assert max(img.size) <= 1920


def test_get_reduced_missing(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "fotos").mkdir()
    assert get_reduced("nonexistent") is None


def test_get_caption(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    fotos = tmp_path / "fotos"
    fotos.mkdir()
    _make_image(fotos / "test.jpg")
    assert get_caption("test") == ""


def test_set_and_get_caption(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    fotos = tmp_path / "fotos"
    fotos.mkdir()
    _make_image(fotos / "test.jpg")
    set_caption("test", "My caption")
    assert get_caption("test") == "My caption"


def test_set_caption_missing_image(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "fotos").mkdir()
    try:
        set_caption("nonexistent", "caption")
        assert False, "should have raised"
    except FileNotFoundError:
        pass
