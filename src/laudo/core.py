import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
import json
from docxtpl import DocxTemplate
from jinja2 import Environment, Template

from laudo.reference_replacer import DocxReferenceReplacer

from .filters import register as register_filters
from .globals import register as register_globals


def _parse_context_txt(folder: Path) -> dict:
    context: dict = {}
    ctx_file = folder / "context.txt"
    if not ctx_file.is_file():
        return context
    for line in ctx_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        if not key:
            continue
        context[key] = val.strip()
    return context


def _read_context_json(folder: Path) -> dict:
    ctx: dict = {}
    for json_file in sorted(folder.glob("*.json")):
        key = json_file.stem.replace(" ", "_")
        content = json_file.read_text(encoding="utf-8")
        ctx[key] = json.loads(content)
    return ctx


def _read_context_markdown(folder: Path, ctx_vars: dict) -> dict:
    ctx: dict = {}
    for md_file in sorted(folder.glob("*.md")):
        key = md_file.stem.replace(" ", "_")
        content = md_file.read_text(encoding="utf-8")
        ctx[key] = Template(content).render(ctx_vars)
    return ctx


def _read_context_pics(folder: Path) -> list[dict]:
    from .exif import get_caption as _get_exif_caption
    from .images import _IMAGE_EXTENSIONS, get_reduced, get_thumbnail

    fotos = folder / "fotos"
    if not fotos.is_dir():
        return []

    cwd = Path.cwd()
    os.chdir(str(folder))
    try:
        pics: list[dict] = []
        for img in sorted(fotos.iterdir()):
            if img.is_file() and img.suffix.lower() in _IMAGE_EXTENSIONS:
                pics.append({
                    "refname": img.stem,
                    "path": img,
                    "caption": _get_exif_caption(img),
                    "thumb": get_thumbnail(img.stem),
                    "reduced": get_reduced(img.stem),
                    "label": "Foto",
                })
        return pics
    finally:
        os.chdir(str(cwd))


def _build_context(folder: Path) -> dict:
    context_folder = folder / "context"
    if not context_folder.is_dir():
        context_folder = folder
    ctx_vars = _parse_context_txt(context_folder)
    ctx_vars.update(_read_context_json(context_folder))
    ctx_vars.update(_read_context_markdown(context_folder, ctx_vars))
    pics = _read_context_pics(folder)
    if pics:
        ctx_vars["pics"] = pics
    return ctx_vars

@dataclass
class RenderEnv:
    tpl: DocxTemplate
    jinja_env: Environment
    temp_folder: Path
    assets_folder: Path

def render_docx(template_path: Path, context: dict, output_path: Path, replace_references=True) -> Path:
    temp_folder = Path(tempfile.mkdtemp(prefix="laudo_"))
    renv = RenderEnv(
        tpl=DocxTemplate(str(template_path)),
        jinja_env=Environment(),
        temp_folder=temp_folder,
        assets_folder=template_path.parent / "assets",
    )
    try:
        register_filters(renv)
        register_globals(renv)
        renv.tpl.render(context, jinja_env=renv.jinja_env)
        if replace_references:
            dr = DocxReferenceReplacer()
            dr.replace_in_doc(renv.tpl.docx)
        renv.tpl.save(str(output_path))
        return output_path
    finally:
        shutil.rmtree(temp_folder, ignore_errors=True)


def run(folder: Path, output: Path, *, debug: bool = False) -> Path:
    template_path = folder / "template.docx"
    if not template_path.is_file():
        raise FileNotFoundError(f"template.docx not found in project folder or in package templates")

    
    context = _build_context(folder)
    if debug:
        import pprint
        print("--- context ---")
        pprint.pprint(context, indent=2, sort_dicts=False)
        print("---------------")

    if output.suffix == ".pdf":
        docx_path = output.with_suffix(".docx")
        render_docx(template_path, context, docx_path)
        from .pdf import convert_to_pdf

        result = convert_to_pdf(docx_path, output)
        docx_path.unlink()
        return result

    return render_docx(template_path, context, output)
