from pathlib import Path

from .core import gen_laudo


def convert(folder: str | Path, output: str | Path, *, debug: bool = False, template: str | Path | None = None) -> Path:
    return gen_laudo(Path(folder), Path(output), debug=debug, template=Path(template) if template else None)
