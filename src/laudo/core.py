<<<<<<< HEAD
import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
import json
from docxtpl import DocxTemplate
from jinja2 import Environment, Template

from laudo.filters.markdown_filter import MarkdownFilter
from laudo.globals.inline_image import InlineImage
from laudo.globals.subdoc_func import SubdocFunc
from laudo.reference_replacer import DocxReferenceReplacer
from laudo.odttpl import Renderer
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
        renv.jinja_env.filters["markdown"] = MarkdownFilter(renv)
        register_filters(renv.jinja_env)

        renv.jinja_env.globals["subdoc"] = SubdocFunc(renv)
        renv.jinja_env.globals["image"] = InlineImage(renv)
        register_globals(renv.jinja_env)
        renv.tpl.render(context, jinja_env=renv.jinja_env)
        if replace_references:
            dr = DocxReferenceReplacer()
            dr.replace_in_doc(renv.tpl.docx)
        renv.tpl.save(str(output_path))
        return output_path
    finally:
        shutil.rmtree(temp_folder, ignore_errors=True)


def render_odt(template_path: Path, context: dict, output_path: Path, replace_references=True) -> Path:
    rd = Renderer()

    register_filters(rd.environment)
    register_globals(rd.environment)

    rd.render(str(template_path), **context)
    rd.save(output_path)
    return output_path


def render_doc(template_path: Path, context: dict, output_path: Path, replace_references=True) -> Path:
    if template_path.suffix == ".docx":
        return render_docx(template_path, context, output_path, replace_references)
    if template_path.suffix == ".odt":
        return render_odt(template_path, context, output_path, replace_references)
    raise ValueError(f"Unsupported template format: {template_path.suffix}")



def gen_laudo(folder: Path, output: Path, *, debug: bool = False, template: Path | None = None) -> Path:
    if template is not None:
        template_path = template
    else:
        template_path = folder / "template.docx"
        if not template_path.is_file():
            template_path = folder / "template.odt"
            if not template_path.is_file():
                raise FileNotFoundError(f"template.docx or template.odt not found in project folder or in package templates")
            
    output = output.with_suffix(template_path.suffix)

    context = _build_context(folder)
    if debug:
        import pprint
        print("--- context ---")
        pprint.pprint(context, indent=2, sort_dicts=False)
        print("---------------")

    if output.suffix == ".pdf":
        doc_path = output.with_suffix(template_path.suffix)
        render_doc(template_path, context, doc_path)
        from .pdf import convert_to_pdf

        result = convert_to_pdf(doc_path, output)
        doc_path.unlink()
        return result

    return render_doc(template_path, context, output)
=======
import os
import re
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
import json
from docxtpl import DocxTemplate
from jinja2 import Environment, Template

from laudo.filters.markdown_filter import MarkdownFilter
from laudo.globals.inline_image import InlineImage
from laudo.globals.subdoc_func import SubdocFunc
from laudo.reference_replacer import DocxReferenceReplacer
from laudo.odttpl import Renderer
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


SECTION_RE = re.compile(r'\[\[(.+?)\]\]')

def _read_markdown(content: str) -> str | dict[str, str]:
    if '[[' not in content:
        return content
    parts = SECTION_RE.split(content)
    sections: dict[str, str] = {}
    for i in range(1, len(parts), 2):
        name = parts[i].strip()
        section_content = parts[i + 1].strip() if i + 1 < len(parts) else ""
        sections[name] = section_content
    return sections

def _read_context_markdown(folder: Path, ctx_vars: dict) -> dict:
    ctx: dict = {}
    for md_file in sorted(folder.glob("*.md")):
        key = md_file.stem.replace(" ", "_")
        content = md_file.read_text(encoding="utf-8")
        rendered = Template(content).render(ctx_vars)
        parts = _read_markdown(rendered)
        if isinstance(parts, dict):
            ctx.update(parts)
        else:
            ctx[key] = parts
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
        renv.jinja_env.filters["markdown"] = MarkdownFilter(renv)
        register_filters(renv.jinja_env)

        renv.jinja_env.globals["subdoc"] = SubdocFunc(renv)
        renv.jinja_env.globals["image"] = InlineImage(renv)
        register_globals(renv.jinja_env)
        renv.tpl.render(context, jinja_env=renv.jinja_env)
        if replace_references:
            dr = DocxReferenceReplacer()
            dr.replace_in_doc(renv.tpl.docx)
        renv.tpl.save(str(output_path))
        return output_path
    finally:
        shutil.rmtree(temp_folder, ignore_errors=True)


def render_odt(template_path: Path, context: dict, output_path: Path, replace_references=True) -> Path:
    rd = Renderer()

    register_filters(rd.environment)
    register_globals(rd.environment)

    rd.render(str(template_path), **context)
    rd.save(output_path)
    return output_path


def render_doc(template_path: Path, context: dict, output_path: Path, replace_references=True) -> Path:
    if template_path.suffix == ".docx":
        return render_docx(template_path, context, output_path, replace_references)
    if template_path.suffix == ".odt":
        return render_odt(template_path, context, output_path, replace_references)
    raise ValueError(f"Unsupported template format: {template_path.suffix}")



def gen_laudo(folder: Path, output: Path, *, debug: bool = False, template: Path | None = None) -> Path:
    if template is not None:
        template_path = template
    else:
        template_path = folder / "template.docx"
        if not template_path.is_file():
            template_path = folder / "template.odt"
            if not template_path.is_file():
                raise FileNotFoundError(f"template.docx or template.odt not found in project folder or in package templates")
            
    output = output.with_suffix(template_path.suffix)

    context = _build_context(folder)
    if debug:
        import pprint
        print("--- context ---")
        pprint.pprint(context, indent=2, sort_dicts=False)
        print("---------------")

    if output.suffix == ".pdf":
        doc_path = output.with_suffix(template_path.suffix)
        render_doc(template_path, context, doc_path)
        from .pdf import convert_to_pdf

        result = convert_to_pdf(doc_path, output)
        doc_path.unlink()
        return result

    return render_doc(template_path, context, output)
>>>>>>> cd4b79770865751ff1f2eb5386c9f21c56f179c8
