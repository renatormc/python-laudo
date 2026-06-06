from pathlib import Path

from .core import gen_laudo


def convert(folder: str | Path, output: str | Path, *, debug: bool | Path = False, template: str | Path | None = None, pos_edit: bool = False) -> Path:
    return gen_laudo(Path(folder), Path(output), debug=debug, template=Path(template) if template else None, pos_edit=pos_edit)
