from dataclasses import dataclass
import os
import re
import shutil
import tempfile
from pathlib import Path
import json
from typing import Tuple
from docxtpl import DocxTemplate
from jinja2 import Environment, Template

from laudo.custom_types import RenderEnv
from laudo.filters.markdown_filter import MarkdownFilter
from laudo.globals.inline_image import InlineImage
from laudo.globals.subdoc_func import SubdocFunc
from laudo.docx_reference_replacer import DocxReferenceReplacer
from .filters import register as register_filters
from .globals import register as register_globals
from .template import get_template


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


IMAGE_GROUP_RE = re.compile(r'image_group\(([^,]+),\s*([^)]+)\)')
IMAGE_RE = re.compile(r'image\(([^,]+)\)')

def _replace_pos_vars(content: str) -> Tuple[str, int]:
    count = 0
    new_text, n = IMAGE_GROUP_RE.subn(r"{{p subdoc('image_group', pics=pics.group('\1'),  cols=\2) }}", content)
    count += n
    new_text, n = IMAGE_RE.subn(r"{{p subdoc('image_group', pics=[pics.get('\1')],  cols=1) }}", new_text)
    count += n
    return new_text, count

@dataclass
class MarkdownContent:
    sections: dict[str, str]
    replaces: int

def _read_context_markdown(folder: Path, ctx_vars: dict) -> MarkdownContent:
    ctx: dict = {}
    for md_file in sorted(folder.glob("*.md")):
        key = md_file.stem.replace(" ", "_")
        content = md_file.read_text(encoding="utf-8")
        content = Template(content).render(ctx_vars)
        content, replaces = _replace_pos_vars(content)
        parts = _read_markdown(content)
        if isinstance(parts, dict):
            ctx.update(parts)
        else:
            ctx[key] = parts
    return MarkdownContent(sections=ctx, replaces=replaces)


class PicsContext:
    def __init__(self, pics: list[dict]) -> None:
        self.pics = pics
        self.pics_map = {p["refname"]: p for p in pics}

    def all(self) -> list[dict]:
        return self.pics

    def group(self, name: str) -> list[dict]:
        ret = [p for p in self.pics if p["group"] == name]
        return ret

    def get(self, refname: str) -> dict | None:
        return self.pics_map.get(refname)

    def __bool__(self) -> bool:
        return bool(self.pics)


def _read_context_pics(folder: Path) -> PicsContext:
    from .images import _IMAGE_EXTENSIONS, get_caption, get_reduced, get_thumbnail

    fotos = folder / "fotos"
    if not fotos.is_dir():
        return PicsContext([])

    cwd = Path.cwd()
    os.chdir(str(folder))
    try:
        pics: list[dict] = []
        for img in fotos.rglob("*"):
            if img.is_file() and img.suffix.lower() in _IMAGE_EXTENSIONS:
                rel = img.relative_to(fotos)
                group = str(rel.parent) if rel.parent != Path(".") else ""
                pics.append({
                    "refname": img.stem,
                    "path": img,
                    "caption": get_caption(img.stem),
                    "thumb": get_thumbnail(img.stem),
                    "reduced": get_reduced(img.stem),
                    "label": "Foto",
                    "group": group,
                })
        pics.sort(key=lambda p: (p["group"], p["refname"]))
        return PicsContext(pics)
    finally:
        os.chdir(str(cwd))

@dataclass
class LaudoContext:
    ctx: dict
    replaces: int

def _build_context(folder: Path) -> LaudoContext:
    context_folder = folder / "context"
    if not context_folder.is_dir():
        context_folder = folder
    ctx_vars = _parse_context_txt(context_folder)
    ctx_vars.update(_read_context_json(context_folder))
    markdown_content = _read_context_markdown(context_folder, ctx_vars)
    ctx_vars.update(markdown_content.sections)
    ctx_vars["pics"] = _read_context_pics(folder)
    return LaudoContext(ctx=ctx_vars, replaces=markdown_content.replaces)


def render_docx(template_path: Path, context: dict, output_path: Path, replace_references=True) -> Path:
    temp_folder = Path(tempfile.mkdtemp(prefix="laudo_"))
    renv = RenderEnv(
        tpl=DocxTemplate(str(template_path)),
        jinja_env=Environment(),
        temp_folder=temp_folder,
    )
    try:
        renv.jinja_env.filters["markdown"] = MarkdownFilter(renv)
        register_filters(renv.jinja_env)

        renv.jinja_env.globals["subdoc"] = SubdocFunc(renv, workdir=Path(output_path).parent)
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


def render_doc(template_path: Path, context: LaudoContext, output_path: Path, replace_references=True) -> Path:
    if context.replaces == 0:
        return render_docx(template_path, context.ctx, output_path, replace_references)
    render_docx(template_path, context.ctx, output_path, False)
    return render_docx(output_path, context.ctx, output_path, replace_references)


def gen_laudo(folder: Path, output: Path, *, debug: bool | Path = False, template: Path | None = None) -> Path:
    if template is not None:
        template_path = template
    else:
        template_path = get_template("template", folder)
    if output.suffix != ".pdf":
        output = output.with_suffix(template_path.suffix)

    context = _build_context(folder)
    if debug:
        if isinstance(debug, Path) and debug.suffix == ".pkl":
            import pickle
            debug.write_bytes(pickle.dumps(context))
            print(f"Context pickled to {debug}")
        else:
            import pprint
            import io
            buf = io.StringIO()
            pprint.pprint(context, indent=2, sort_dicts=False, stream=buf)
            formatted = buf.getvalue()
            if isinstance(debug, Path):
                debug.write_text(formatted, encoding="utf-8")
                print(f"Context written to {debug}")
            else:
                print("--- context ---")
                print(formatted)
                print("---------------")
    if output.suffix == ".pdf":
        doc_path = output.with_suffix(template_path.suffix)
        render_doc(template_path, context, doc_path)
        from .pdf import convert_to_pdf

        result = convert_to_pdf(doc_path, output)
        doc_path.unlink()
        return result

    return render_doc(template_path, context, output)
