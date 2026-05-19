from pathlib import Path

import pytest
from PIL import Image
from docx import Document


@pytest.fixture
def template_path(tmp_path: Path) -> Path:
    path = tmp_path / "template.docx"
    doc = Document()
    
    doc.save(str(path))
    return path


@pytest.fixture
def sample_project(tmp_path: Path) -> Path:
    folder = tmp_path / "project"
    folder.mkdir()

    doc = Document()
    doc.save(str(folder / "template.docx"))

    (folder / "intro.md").write_text("# Introduction\nHello world.", encoding="utf-8")
    (folder / "chapter 1.md").write_text("## Chapter One\nContent here.", encoding="utf-8")
    (folder / "context.txt").write_text("author = John Doe\ntitle = My Doc\n", encoding="utf-8")

    fotos = folder / "fotos"
    fotos.mkdir()
    Image.new("RGB", (100, 100)).save(str(fotos / "logo.png"))
    Image.new("RGB", (200, 150)).save(str(fotos / "photo.jpg"))

    return folder
