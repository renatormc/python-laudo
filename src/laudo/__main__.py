import os
import stat
from pathlib import Path

import click

from . import convert


def _find_project_root() -> Path:
    candidate = Path(__file__).resolve()
    for parent in [candidate] + list(candidate.parents):
        if (parent / "pyproject.toml").is_file():
            return parent
    return candidate.parent


def _install() -> None:
    bindir = Path.home() / ".local" / "bin"
    bindir.mkdir(parents=True, exist_ok=True)
    script = bindir / "laudo"
    project_root = _find_project_root()
    content = f"""#!/usr/bin/env bash
exec uv run --project {project_root} laudo "$@"
"""
    script.write_text(content.lstrip())
    script.chmod(script.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    click.echo(f"Installed laudo wrapper at {script}")
    if str(bindir) not in os.environ.get("PATH", "").split(":"):
        click.echo(f"Warning: {bindir} is not in your PATH.", err=True)
        shell = Path(os.environ.get("SHELL", "/bin/bash")).name
        rc: Path | None = (
            Path.home() / ".bashrc"
            if shell == "bash"
            else Path.home() / ".zshrc"
            if shell == "zsh"
            else None
        )
        if rc is not None:
            click.echo(f"Add this line to {rc}:")
            click.echo(f'  export PATH="$PATH:{bindir}"')


@click.command()
@click.option("--install", is_flag=True, help="Install the laudo wrapper script to ~/.local/bin/laudo")
@click.option("--dir", "dir_", type=click.Path(exists=True, file_okay=False, path_type=Path), default=None, help="Working directory (default: current directory)")
@click.option("--gui", is_flag=True, help="Open the caption editor GUI")
@click.option("--debug", is_flag=True, help="Print the template context before rendering")
def main(install: bool, dir_: Path | None, gui: bool, debug: bool) -> None:
    """Convert markdown files or open the caption editor."""
    if install:
        _install()
        return
    if dir_ is not None:
        os.chdir(str(dir_))
    if gui:
        from .gui import run as run_gui

        run_gui(Path.cwd())
        return
    folder = Path.cwd()
    output = folder / "laudo.docx"
    result = convert(folder, output, debug=debug)
    click.echo(f"Generated: {result}")


if __name__ == "__main__":
    main()
