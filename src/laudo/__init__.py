from pathlib import Path

from .core import run


def convert(folder: str | Path, output: str | Path, *, debug: bool = False) -> Path:
    return run(Path(folder), Path(output), debug=debug)
