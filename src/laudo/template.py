import os
from pathlib import Path



def get_template(name: str, workdir: Path) -> Path:
    candidate = workdir / f"{name}.docx"
    if candidate.is_file():
        return candidate

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
                

    raise FileNotFoundError(
        f"Template '{name}.docx' not found in {workdir}"
    )
