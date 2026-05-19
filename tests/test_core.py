from pathlib import Path

from laudo.core import _build_context, _read_context_json, _read_context_markdown, _read_context_pics, render_docx


def test_build_context_empty(tmp_path: Path):
    folder = tmp_path / "empty"
    folder.mkdir()
    ctx = _build_context(folder)
    assert ctx == {}


def test_build_context_md_files(sample_project: Path):
    ctx = _build_context(sample_project)
    assert ctx["intro"] == "# Introduction\nHello world."
    assert ctx["chapter_1"] == "## Chapter One\nContent here."


def test_build_context_context_txt(sample_project: Path):
    ctx = _build_context(sample_project)
    assert ctx["author"] == "John Doe"
    assert ctx["title"] == "My Doc"


def test_build_context_md_substitutes_vars(tmp_path: Path):
    folder = tmp_path / "proj"
    folder.mkdir()
    (folder / "context.txt").write_text("name = John\n", encoding="utf-8")
    (folder / "greeting.md").write_text("Hello {{ name }}!", encoding="utf-8")
    ctx = _build_context(folder)
    assert ctx["greeting"] == "Hello John!"


def test_build_context_context_txt_skips_invalid(tmp_path: Path):
    folder = tmp_path / "proj"
    folder.mkdir()
    (folder / "context.txt").write_text(
        "valid = yes\n\n=bad\nnoequal\nkey= value\n", encoding="utf-8"
    )
    ctx = _build_context(folder)
    assert ctx == {"valid": "yes", "key": "value"}


def test_read_context_json(tmp_path: Path):
    folder = tmp_path / "proj"
    folder.mkdir()
    (folder / "data.json").write_text('{"foo": "bar"}', encoding="utf-8")
    ctx = _read_context_json(folder)
    assert ctx == {"data": {"foo": "bar"}}


def test_read_context_markdown(tmp_path: Path):
    folder = tmp_path / "proj"
    folder.mkdir()
    (folder / "hello.md").write_text("# Hello {{ name }}", encoding="utf-8")
    ctx = _read_context_markdown(folder, {"name": "World"})
    assert ctx["hello"] == "# Hello World"


def test_read_context_pics(sample_project: Path, monkeypatch):
    monkeypatch.chdir(sample_project)
    pics = _read_context_pics(sample_project)
    assert isinstance(pics, list)
    assert len(pics) == 2
    stems = {p["refname"] for p in pics}
    assert stems == {"logo", "photo"}
    logo = next(p for p in pics if p["refname"] == "logo")
    assert logo["caption"] == ""
    assert logo["path"].name == "logo.png"
    assert logo["thumb"] is not None
    assert logo["thumb"].is_file()
    assert logo["reduced"] is not None


def test_build_context_pics_no_fotos(tmp_path: Path):
    folder = tmp_path / "proj"
    folder.mkdir()
    (folder / "readme.md").write_text("# Hi", encoding="utf-8")
    ctx = _build_context(folder)
    assert "pics" not in ctx


def test_render_docx(template_path: Path, tmp_path: Path):
    output = tmp_path / "out.docx"
    context = {"name": "World"}
    result = render_docx(template_path, context, output)
    assert result == output
    assert output.is_file()
    assert output.stat().st_size > 0


def test_render_docx_with_markdown_filter(template_path: Path, tmp_path: Path):
    output = tmp_path / "out.docx"
    context = {"intro": "# Hello"}
    result = render_docx(template_path, context, output)
    assert result.is_file()
