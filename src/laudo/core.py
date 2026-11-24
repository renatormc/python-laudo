import json
import re
import shutil
import tempfile
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from docxtpl import DocxTemplate
from jinja2 import Template

from .docx_reference_replacer import DocxReferenceReplacer, raise_reference_errors
from .errors import ImageNotFoundError, LaudoError
from .render_env import create_render_env
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


# Both macros expand to a paragraph-level {{p ...}} tag, which replaces the whole
# paragraph, so they must sit alone on their own line.
IMAGE_GROUP_RE = re.compile(r'^[ \t]*image_group\([ \t]*([^,()\n]+?)[ \t]*,[ \t]*(\d+|[A-Za-z_]\w*)[ \t]*\)[ \t]*$', re.MULTILINE)
IMAGE_RE = re.compile(r'^[ \t]*image\([ \t]*([^,()\n]+?)[ \t]*\)[ \t]*$', re.MULTILINE)
_MACRO_LEFTOVER_RE = re.compile(r'\bimage(?:_group)?\(')


def _image_group_tag(m: re.Match[str]) -> str:
    return f"{{{{p subdoc('image_group', pics=pics.require_group({m.group(1)!r}), cols={m.group(2)}|int) }}}}"


def _image_tag(m: re.Match[str]) -> str:
    return f"{{{{p subdoc('image_group', pics=[pics.require({m.group(1)!r})], cols=1) }}}}"


def _replace_pos_vars(content: str) -> tuple[str, int]:
    new_text, n_groups = IMAGE_GROUP_RE.subn(_image_group_tag, content)
    new_text, n_images = IMAGE_RE.subn(_image_tag, new_text)
    for line in new_text.splitlines():
        if _MACRO_LEFTOVER_RE.search(line) and "subdoc('image_group'" not in line:
            raise LaudoError(
                f"Uso inválido de image/image_group na linha: {line.strip()!r}. "
                "Escreva image(nome) ou image_group(grupo, colunas) sozinho na linha."
            )
    return new_text, n_groups + n_images

@dataclass
class MarkdownContent:
    sections: dict[str, str]
    replaces: int

def _read_context_markdown(folder: Path, ctx_vars: dict) -> MarkdownContent:
    ctx: dict = {}
    replaces = 0
    for md_file in sorted(folder.glob("*.md")):
        key = md_file.stem.replace(" ", "_")
        content = md_file.read_text(encoding="utf-8")
        content = Template(content).render(ctx_vars)
        content, n = _replace_pos_vars(content)
        replaces += n
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

    def require(self, refname: str) -> dict:
        refname = refname.strip()
        pic = self.pics_map.get(refname)
        if pic is None:
            raise ImageNotFoundError(
                f"Imagem '{refname}' usada em image({refname}) não encontrada na pasta fotos/. "
                f"{self._available_hint()}"
            )
        return pic

    def require_group(self, name: str) -> list[dict]:
        name = name.strip()
        pics = self.group(name)
        if not pics:
            groups = sorted({p["group"] for p in self.pics if p["group"]})
            hint = f"Grupos disponíveis: {', '.join(groups)}." if groups else "Nenhuma subpasta com imagens em fotos/."
            raise ImageNotFoundError(
                f"Grupo de imagens '{name}' usado em image_group({name}, ...) não encontrado "
                f"(esperado: fotos/{name}/ com imagens). {hint}"
            )
        return pics

    def _available_hint(self) -> str:
        if not self.pics:
            return "A pasta fotos/ não existe ou não contém imagens."
        names = [p["refname"] for p in self.pics]
        shown = ", ".join(names[:15])
        more = f" (e mais {len(names) - 15})" if len(names) > 15 else ""
        return f"Imagens disponíveis: {shown}{more}."

    def __bool__(self) -> bool:
        return bool(self.pics)


def _read_context_pics(folder: Path) -> PicsContext:
    from concurrent.futures import ThreadPoolExecutor

    from . import db
    from .images import list_images, reduced_for, thumbnail_for

    fotos = folder / "fotos"
    images = list_images(folder)
    if not images:
        return PicsContext([])

    captions = db.get_captions(folder)  # one query instead of one connection per image

    def build(img: Path) -> dict:
        rel = img.relative_to(fotos)
        reduced = reduced_for(img, folder)
        return {
            "refname": img.stem,
            "path": img,
            "caption": captions.get(img.stem, ""),
            # resizing the (already small) reduced copy is much cheaper than the original
            "thumb": thumbnail_for(img, folder, source=reduced),
            "reduced": reduced,
            "label": "Foto",
            "group": str(rel.parent) if rel.parent != Path(".") else "",
        }

    # Pillow releases the GIL while decoding/resizing, so threads scale on new images.
    with ThreadPoolExecutor() as pool:
        pics = list(pool.map(build, images))
    pics.sort(key=lambda p: (p["group"], p["refname"]))
    return PicsContext(pics)


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


def _json_default(obj: object) -> object:
    if isinstance(obj, PicsContext):
        return obj.all()
    if isinstance(obj, Path):
        return str(obj)
    return repr(obj)


def context_to_json(ctx: dict) -> str:
    return json.dumps(ctx, indent=2, ensure_ascii=False, default=_json_default)


def _render_to_bytes(source: Path | bytes, context: dict, workdir: Path, replace_references: bool) -> bytes:
    temp_folder = Path(tempfile.mkdtemp(prefix="laudo_"))
    try:
        tpl = DocxTemplate(BytesIO(source) if isinstance(source, bytes) else str(source))
        renv = create_render_env(tpl, temp_folder, workdir)
        tpl.render(context, jinja_env=renv.jinja_env)
        if replace_references:
            raise_reference_errors(DocxReferenceReplacer().replace_in_doc(tpl.docx))
        buf = BytesIO()
        tpl.save(buf)
        return buf.getvalue()
    finally:
        shutil.rmtree(temp_folder, ignore_errors=True)


def render_docx(
    template_path: Path,
    context: dict,
    output_path: Path,
    replace_references: bool = True,
    *,
    workdir: Path | None = None,
) -> Path:
    workdir = workdir or Path(output_path).parent
    output_path.write_bytes(_render_to_bytes(template_path, context, workdir, replace_references))
    return output_path


def render_doc(
    template_path: Path,
    context: LaudoContext,
    output_path: Path,
    replace_references: bool = True,
    *,
    workdir: Path | None = None,
) -> Path:
    workdir = workdir or Path(output_path).parent
    if context.replaces == 0:
        data = _render_to_bytes(template_path, context.ctx, workdir, replace_references)
    else:
        # The markdown expanded into {{p subdoc(...)}} tags; a second pass renders them.
        # The intermediate document stays in memory instead of round-tripping through disk.
        first = _render_to_bytes(template_path, context.ctx, workdir, False)
        data = _render_to_bytes(first, context.ctx, workdir, replace_references)
    output_path.write_bytes(data)
    return output_path


def gen_laudo(folder: Path, output: Path, *, debug: bool | Path = False, template: Path | None = None, pos_edit: bool = False) -> Path:
    template_path = template if template is not None else get_template("template", folder)
    if output.suffix != ".pdf":
        output = output.with_suffix(template_path.suffix)

    context = _build_context(folder)
    if debug:
        _write_debug(context, debug)
    if output.suffix == ".pdf":
        from .pdf import convert_to_pdf

        doc_path = output.with_suffix(template_path.suffix)
        render_doc(template_path, context, doc_path, replace_references=not pos_edit, workdir=folder)
        result = convert_to_pdf(doc_path, output)
        doc_path.unlink()
        return result

    return render_doc(template_path, context, output, replace_references=not pos_edit, workdir=folder)


def _write_debug(context: LaudoContext, debug: bool | Path) -> None:
    if isinstance(debug, Path) and debug.suffix == ".pkl":
        import pickle

        debug.write_bytes(pickle.dumps(context))
        print(f"Context pickled to {debug}")
        return
    import pprint

    formatted = pprint.pformat(context, indent=2, sort_dicts=False)
    if isinstance(debug, Path):
        debug.write_text(formatted, encoding="utf-8")
        print(f"Context written to {debug}")
    else:
        print("--- context ---")
        print(formatted)
        print("---------------")
