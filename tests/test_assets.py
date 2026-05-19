from pathlib import Path

from laudo.assets import collect_assets


def test_collect_assets_empty(tmp_path: Path):
    assert collect_assets(tmp_path / "nonexistent") == {}
    assert collect_assets(tmp_path / "empty_dir") == {}


def test_collect_assets(tmp_path: Path):
    d = tmp_path / "assets"
    d.mkdir()
    (d / "img1.png").write_text("fake")
    (d / "img2.jpg").write_text("fake")
    (d / "notes.txt").write_text("skip me")

    result = collect_assets(d)
    assert set(result.keys()) == {"img1", "img2", "notes"}
    assert result["img1"] == {"path": d / "img1.png", "caption": ""}
    assert result["img2"] == {"path": d / "img2.jpg", "caption": ""}
    assert result["notes"] == {"path": d / "notes.txt", "caption": ""}


def test_collect_assets_sorted(tmp_path: Path):
    d = tmp_path / "assets"
    d.mkdir()
    (d / "b.png").write_text("")
    (d / "a.png").write_text("")
    (d / "c.png").write_text("")

    result = collect_assets(d)
    assert list(result.keys()) == ["a", "b", "c"]
