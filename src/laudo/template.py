import os
from pathlib import Path

from laudo.errors import TemplateNotFoundError


BUILTIN_TEMPLATES_DIR = Path(__file__).parent / "templates"


def get_template(name: str, workdir: Path) -> Path:
    searched: list[Path] = []

    candidate = workdir / f"{name}.docx"
    if candidate.is_file():
        return candidate
    searched.append(candidate)

    template_ref = workdir / ".laudo" / ".template"
    if template_ref.is_file():
        tpl_name = Path(template_ref.read_text(encoding="utf-8").strip()).stem
        templates_dir = os.environ.get("LAUDOS_TEMPLATES_FOLDER")
        if templates_dir:
            templates_path = Path(templates_dir)
            if templates_path.is_dir():
                template_path = templates_path / tpl_name / f"{name}.docx"
                if template_path.is_file():
                    return template_path
                searched.append(template_path)

    builtin = BUILTIN_TEMPLATES_DIR / f"{name}.docx"
    if builtin.is_file():
        return builtin
    searched.append(builtin)

    locations = "\n".join(f"  - {p}" for p in searched)
    raise TemplateNotFoundError(
        f"Template '{name}.docx' não encontrado. Locais procurados:\n{locations}"
    )
