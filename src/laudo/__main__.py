import argparse
import json
import os
import shutil
import stat
import sys
from pathlib import Path

from . import convert
from .core import _build_context, _parse_context_txt, context_to_json
from .errors import LaudoError


def _find_project_root() -> Path:
    candidate = Path(__file__).resolve()
    for parent in [candidate] + list(candidate.parents):
        if (parent / "pyproject.toml").is_file():
            return parent
    return candidate.parent


def _cmd_install() -> None:
    bindir = Path.home() / ".local" / "bin"
    bindir.mkdir(parents=True, exist_ok=True)
    project_root = _find_project_root()

    if os.name == "nt":
        script = bindir / "laudo.bat"
        content = f"@uv run --project {project_root} laudo %*\n"
        script.write_text(content.lstrip())
        print(f"Installed laudo wrapper at {script}")
        path_sep = ";"
        path_hint = f"set PATH={bindir};%PATH%"
    else:
        script = bindir / "laudo-dev"
        content = f"#!/usr/bin/env bash\nexec uv run --project {project_root} laudo \"$@\"\n"
        script.write_text(content.lstrip())
        script.chmod(script.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        print(f"Installed laudo wrapper at {script}")
        path_sep = ":"
        path_hint = f'export PATH="$PATH:{bindir}"'

    if str(bindir) not in os.environ.get("PATH", "").split(path_sep):
        print(f"Warning: {bindir} is not in your PATH.", file=sys.stderr)
        if os.name == "nt":
            print("Add this to your PATH (Command Prompt: set PATH=... or via System Settings):")
            print(f"  {path_hint}")
        else:
            shell = Path(os.environ.get("SHELL", "/bin/bash")).name
            rc: Path | None = (
                Path.home() / ".bashrc"
                if shell == "bash"
                else Path.home() / ".zshrc"
                if shell == "zsh"
                else None
            )
            if rc is not None:
                print(f"Add this line to {rc}:")
                print(f"  {path_hint}")


def _enter_dir(dir_: Path | None) -> Path:
    """chdir into ``dir_`` (when given) and return the project folder."""
    if dir_ is not None:
        os.chdir(str(dir_))
    return Path.cwd()


def _write_template_name(folder: Path, name: str) -> None:
    laudo_dir = folder / ".laudo"
    laudo_dir.mkdir(parents=True, exist_ok=True)
    (laudo_dir / ".template").write_text(f"{name}\n", encoding="utf-8")
    print(f"Template '{name}' set for {folder}")


def _cmd_gen(dir_: Path | None, debug: Path | bool, pdf: bool, output: Path | None, template: Path | None, pos_edit: bool) -> None:
    folder = _enter_dir(dir_)
    if output is None:
        output = folder / ("laudo.pdf" if pdf else "laudo.docx")
    result = convert(folder, output, debug=debug, template=template, pos_edit=pos_edit)
    print(f"Generated: {result}")


def _cmd_captions(dir_: Path | None) -> None:
    from .gui import run as run_gui

    run_gui(_enter_dir(dir_))


def _cmd_gui(dir_: Path | None) -> None:
    from .gui import run_main

    run_main(dir_.resolve() if dir_ is not None else None)


def _cmd_template(dir_: Path | None, name: str) -> None:
    _write_template_name(_enter_dir(dir_), name)


def _cmd_vars(dir_: Path | None) -> None:
    print(json.dumps(_parse_context_txt(_enter_dir(dir_)), indent=2, ensure_ascii=False))


def _cmd_context(dir_: Path | None, output: Path | None) -> None:
    if output is not None:
        output = output.resolve()
    formatted = context_to_json(_build_context(_enter_dir(dir_)).ctx)
    if output is not None:
        output.write_text(formatted, encoding="utf-8")
        print(f"Context written to {output}")
    else:
        print(formatted)


def _cmd_init(dir_: Path | None, name: str) -> None:
    folder = _enter_dir(dir_)
    _write_template_name(folder, name)

    templates_dir = os.environ.get("LAUDOS_TEMPLATES_FOLDER")
    if not templates_dir:
        print("LAUDOS_TEMPLATES_FOLDER not set, skipping file copy")
        return

    src = Path(templates_dir) / name
    if not src.is_dir():
        print(f"Template folder not found: {src}, skipping file copy")
        return

    copied = 0
    for item in src.iterdir():
        if item.is_file() and item.suffix != ".docx":
            shutil.copy2(item, folder / item.name)
            copied += 1

    print(f"Copied {copied} file(s) from {src} to {folder}")


def _ask_max_resolution() -> int:
    from .reduce import DEFAULT_RESOLUTION, RESOLUTION_CHOICES

    if not sys.stdin.isatty():
        return DEFAULT_RESOLUTION
    import inquirer  # type: ignore[import-untyped]

    question = inquirer.List(
        "max_resolution",
        message="Maximum width/height in pixels",
        choices=[(f"{r}px", r) for r in RESOLUTION_CHOICES],
        default=DEFAULT_RESOLUTION,
    )
    answers = inquirer.prompt([question])
    if answers is None:
        sys.exit(1)
    return int(answers["max_resolution"])


def _cmd_reduce_images(source: Path, dest: Path, max_resolution: int | None) -> None:
    from .reduce import reduce_images

    if max_resolution is None:
        max_resolution = _ask_max_resolution()
    try:
        reduce_images(source, dest, max_resolution=max_resolution)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    print(f"Reduced images saved to {dest}")


def _existing_dir(value: str) -> Path:
    p = Path(value)
    if not p.is_dir():
        raise argparse.ArgumentTypeError(f"not a directory: {value}")
    return p


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert markdown files or open the caption editor."
    )
    sub = parser.add_subparsers(dest="command")

    gen_p = sub.add_parser("gen", help="Generate docx/pdf from markdown files.")
    gen_p.add_argument("--dir", type=_existing_dir, default=None, help="Working directory (default: current directory)")
    gen_p.add_argument("--debug", nargs="?", const=True, default=None, type=Path, help="Print the template context before rendering, or write to a file if a path is provided")
    gen_p.add_argument("--pdf", action="store_true", help="Generate PDF instead of DOCX (requires pandoc)")
    gen_p.add_argument("--output", type=Path, default=None, help="Output file path (default: laudo.docx or laudo.pdf in working directory)")
    gen_p.add_argument("--template", type=Path, default=None, help="Path to template file (default: template.docx in project folder)")
    gen_p.add_argument("--pos-edit", action="store_true", help="Enable position-based editing")
    cap_p = sub.add_parser("captions", help="Open the caption editor GUI.")
    cap_p.add_argument("--dir", type=_existing_dir, default=None, help="Working directory (default: current directory)")

    gui_p = sub.add_parser("gui", help="Open the main GUI (default when no command is given).")
    gui_p.add_argument("--dir", type=_existing_dir, default=None, help="Working directory (default: current directory)")

    tpl_p = sub.add_parser("template", help="Set the template name for the current folder (creates .template file).")
    tpl_p.add_argument("name", help="Template name (without extension)")
    tpl_p.add_argument("--dir", type=_existing_dir, default=None, help="Working directory (default: current directory)")

    vars_p = sub.add_parser("vars", help="Print context.txt variables as JSON.")
    vars_p.add_argument("--dir", type=_existing_dir, default=None, help="Working directory (default: current directory)")

    ctx_p = sub.add_parser("context", help="Print the template context used to render the docx as JSON.")
    ctx_p.add_argument("output", nargs="?", type=Path, default=None, help="Save the context as JSON to this file instead of printing it")
    ctx_p.add_argument("--dir", type=_existing_dir, default=None, help="Working directory (default: current directory)")

    init_p = sub.add_parser("init", help="Initialize project from a template: saves template name and copies template files.")
    init_p.add_argument("name", help="Template name (without extension)")
    init_p.add_argument("--dir", type=_existing_dir, default=None, help="Working directory (default: current directory)")

    red_p = sub.add_parser("reduce-images", help="Reduce image sizes in a folder or inside a .docx file.")
    red_p.add_argument("source", type=Path, help="Source folder or .docx file")
    red_p.add_argument("dest", type=Path, help="Destination folder or .docx file (may be the same as source)")
    red_p.add_argument("--max", dest="max_resolution", type=int, default=None, help="Maximum width/height in pixels (prompted if omitted)")

    sub.add_parser("install", help="Install the laudo wrapper script to ~/.local/bin.")

    args = parser.parse_args()

    if args.command is None:
        _cmd_gui(None)
        return

    try:
        _dispatch(args)
    except LaudoError as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)


def _dispatch(args: argparse.Namespace) -> None:
    match args.command:
        case "install":
            _cmd_install()
        case "gen":
            _cmd_gen(args.dir, args.debug, args.pdf, args.output, args.template, args.pos_edit)
        case "captions":
            _cmd_captions(args.dir)
        case "gui":
            _cmd_gui(args.dir)
        case "template":
            _cmd_template(args.dir, args.name)
        case "vars":
            _cmd_vars(args.dir)
        case "context":
            _cmd_context(args.dir, args.output)
        case "init":
            _cmd_init(args.dir, args.name)
        case "reduce-images":
            _cmd_reduce_images(args.source, args.dest, args.max_resolution)


if __name__ == "__main__":
    main()
