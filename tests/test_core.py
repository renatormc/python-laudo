from pathlib import Path

from PIL import Image

from laudo.core import (
    PicsContext,
    _build_context,
    _read_context_json,
    _read_context_markdown,
    _read_context_pics,
    _read_markdown,
    _replace_pos_vars,
    render_docx,
)


def test_build_context_empty(tmp_path: Path):
    folder = tmp_path / "empty"
    folder.mkdir()
    ctx = _build_context(folder).ctx
    assert isinstance(ctx.get("pics"), PicsContext)
    assert not ctx["pics"]


def test_build_context_md_files(sample_project: Path):
    ctx = _build_context(sample_project).ctx
    assert ctx["intro"] == "# Introduction\nHello world."
    assert ctx["chapter_1"] == "## Chapter One\nContent here."


def test_build_context_context_txt(sample_project: Path):
    ctx = _build_context(sample_project).ctx
    assert ctx["author"] == "John Doe"
    assert ctx["title"] == "My Doc"


def test_build_context_md_substitutes_vars(tmp_path: Path):
    folder = tmp_path / "proj"
    folder.mkdir()
    (folder / "context.txt").write_text("name = John\n", encoding="utf-8")
    (folder / "greeting.md").write_text("Hello {{ name }}!", encoding="utf-8")
    ctx = _build_context(folder).ctx
    assert ctx["greeting"] == "Hello John!"


def test_build_context_context_txt_skips_invalid(tmp_path: Path):
    folder = tmp_path / "proj"
    folder.mkdir()
    (folder / "context.txt").write_text(
        "valid = yes\n\n=bad\nnoequal\nkey= value\n", encoding="utf-8"
    )
    ctx = _build_context(folder).ctx
    assert ctx["valid"] == "yes"
    assert ctx["key"] == "value"


def test_read_context_json(tmp_path: Path):
    folder = tmp_path / "proj"
    folder.mkdir()
    (folder / "data.json").write_text('{"foo": "bar"}', encoding="utf-8")
    ctx = _read_context_json(folder)
    assert ctx == {"data": {"foo": "bar"}}


def test_replace_pos_vars():
    result = _replace_pos_vars("image_group(name, 3)")
    expected = ("{{p subdoc('image_group', pics=pics.require_group('name'), cols=3|int) }}", 1)
    assert result == expected, f"Expected {expected!r}, got {result!r}"
    # cols may be a context variable (context.txt values are strings, hence |int)
    result = _replace_pos_vars("xx\n  image_group( a , cols )  \nyy")
    expected = ("xx\n{{p subdoc('image_group', pics=pics.require_group('a'), cols=cols|int) }}\nyy", 1)
    assert result == expected, f"Expected {expected!r}, got {result!r}"
    result = _replace_pos_vars("image(foto 1)")
    expected = ("{{p subdoc('image_group', pics=[pics.require('foto 1')], cols=1) }}", 1)
    assert result == expected, f"Expected {expected!r}, got {result!r}"
    assert _replace_pos_vars("no match here") == ("no match here", 0)
    assert _replace_pos_vars("") == ("", 0)


def test_replace_pos_vars_rejects_macro_inside_text():
    import pytest
    from laudo.errors import LaudoError

    for line in ("Veja image(foto1) abaixo", "image(a) e image(b)", "image_group(local)", "image_group(a, 2) fim"):
        with pytest.raises(LaudoError, match="sozinho na linha"):
            _replace_pos_vars(f"texto\n{line}\n")


def test_image_group_supports_any_number_of_columns(tmp_path: Path):
    import zipfile

    from docx import Document
    from lxml import etree

    from laudo import convert

    project = tmp_path / "proj"
    grupo = project / "fotos" / "grupo"
    grupo.mkdir(parents=True)
    for i in range(5):
        Image.new("RGB", (40, 30)).save(str(grupo / f"x{i}.jpg"))
    doc = Document()
    doc.add_paragraph("{{p laudo|markdown }}")
    doc.save(str(project / "template.docx"))

    for cols in (1, 2, 3, 4):
        (project / "laudo.md").write_text(f"image_group(grupo, {cols})\n", encoding="utf-8")
        out = convert(project, project / f"out{cols}.docx")
        xml = zipfile.ZipFile(out).read("word/document.xml")
        etree.fromstring(xml)
        assert xml.count(b"<pic:pic") == 5, f"cols={cols}"
        assert b"Foto 5" in xml


def test_pics_require_missing_gives_clear_error():
    import pytest
    from laudo.errors import ImageNotFoundError

    pics = PicsContext([{"refname": "a", "group": "g"}])
    assert pics.require(" a ")["refname"] == "a"
    with pytest.raises(ImageNotFoundError, match="Imagem 'loc'.*Imagens disponíveis: a"):
        pics.require("loc")
    with pytest.raises(ImageNotFoundError, match="Grupo de imagens 'x'.*Grupos disponíveis: g"):
        pics.require_group("x")
    with pytest.raises(ImageNotFoundError, match="fotos/ não existe"):
        PicsContext([]).require("loc")


def test_read_markdown_no_sections():
    content = "# Hello World\n\nThis is a test."
    result = _read_markdown(content)
    assert result == content


def test_read_markdown_with_sections():
    content = "[[historico]]\n\n# teste\n\nAqui vai um teste.\n\n[[conclusao]]\n\nAqui vai a conclusão"
    result = _read_markdown(content)
    assert isinstance(result, dict)
    assert "historico" in result
    assert "conclusao" in result
    assert "# teste" in result["historico"]
    assert "Aqui vai um teste." in result["historico"]
    assert "Aqui vai a conclusão" in result["conclusao"]


def test_read_markdown_with_jinja_substitution():
    content = "[[section_a]]\nHello {{ name }}\n[[section_b]]\nGoodbye {{ name }}"
    result = _read_markdown(content)
    assert isinstance(result, dict)
    assert "section_a" in result
    assert "section_b" in result


def test_read_context_markdown_with_sections(tmp_path: Path):
    folder = tmp_path / "proj"
    folder.mkdir()
    content = "[[historico]]\n# Histórico\n\nConteúdo histórico.\n\n[[conclusao]]\n# Conclusão\n\nConclusão do caso."
    (folder / "report.md").write_text(content, encoding="utf-8")
    ctx = _read_context_markdown(folder, {}).sections
    assert "historico" in ctx
    assert "conclusao" in ctx
    assert "# Histórico" in ctx["historico"]
    assert "Conclusão do caso." in ctx["conclusao"]


def test_read_context_markdown(tmp_path: Path):
    folder = tmp_path / "proj"
    folder.mkdir()
    (folder / "hello.md").write_text("# Hello {{ name }}", encoding="utf-8")
    ctx = _read_context_markdown(folder, {"name": "World"}).sections
    assert ctx["hello"] == "# Hello World"


def test_read_context_pics(sample_project: Path, monkeypatch):
    monkeypatch.chdir(sample_project)
    pics_ctx = _read_context_pics(sample_project)
    assert isinstance(pics_ctx, PicsContext)
    assert len(pics_ctx.pics) == 2
    stems = {p["refname"] for p in pics_ctx.pics}
    assert stems == {"logo", "photo"}
    logo = next(p for p in pics_ctx.pics if p["refname"] == "logo")
    assert logo["caption"] == ""
    assert logo["path"].name == "logo.png"
    assert logo["thumb"] is not None
    assert logo["thumb"].is_file()
    assert logo["reduced"] is not None
    assert logo["group"] == ""
    assert pics_ctx.pics_map["logo"] is logo
    assert pics_ctx.get("logo") is logo
    assert pics_ctx.get("nonexistent") is None
    assert bool(pics_ctx) is True


def test_read_context_pics_empty(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    pics_ctx = _read_context_pics(tmp_path)
    assert isinstance(pics_ctx, PicsContext)
    assert len(pics_ctx.pics) == 0
    assert bool(pics_ctx) is False


def test_read_context_pics_subfolders(tmp_path: Path, monkeypatch):
    folder = tmp_path / "proj"
    folder.mkdir()
    (folder / "template.docx").write_text("tpl", encoding="utf-8")
    fotos = folder / "fotos"
    fotos.mkdir()
    Image.new("RGB", (10, 10)).save(str(fotos / "a.jpg"))
    sub = fotos / "events"
    sub.mkdir()
    Image.new("RGB", (10, 10)).save(str(sub / "b.jpg"))
    sub2 = fotos / "events" / "party"
    sub2.mkdir(parents=True)
    Image.new("RGB", (10, 10)).save(str(sub2 / "c.jpg"))

    monkeypatch.chdir(folder)
    pics_ctx = _read_context_pics(folder)
    assert len(pics_ctx.pics) == 3
    groups = [(p["refname"], p["group"]) for p in pics_ctx.pics]
    assert groups == [
        ("a", ""),
        ("b", "events"),
        ("c", str(Path("events/party"))),
    ]


def test_build_context_pics_no_fotos(tmp_path: Path):
    folder = tmp_path / "proj"
    folder.mkdir()
    (folder / "readme.md").write_text("# Hi", encoding="utf-8")
    ctx = _build_context(folder).ctx
    assert isinstance(ctx.get("pics"), PicsContext)
    assert not ctx["pics"]


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


def test_subdoc_with_images_produces_valid_xml(sample_project: Path, tmp_path: Path):
    """Images inserted via subdoc must keep their namespace declarations (xmlns:a)."""
    import zipfile

    from docx import Document
    from lxml import etree

    template = tmp_path / "tpl.docx"
    doc = Document()
    doc.add_paragraph("{{p subdoc('image_group', pics=pics.all(), cols=2) }}")
    doc.save(str(template))

    ctx = _build_context(sample_project).ctx
    output = render_docx(template, ctx, tmp_path / "out.docx", replace_references=False, workdir=sample_project)

    xml = zipfile.ZipFile(output).read("word/document.xml")
    etree.fromstring(xml)  # raises XMLSyntaxError on undeclared prefixes
    assert xml.count(b"<pic:pic") == 2
    Document(str(output))  # python-docx can reopen it
