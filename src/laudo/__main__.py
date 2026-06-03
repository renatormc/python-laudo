import argparse
import json
import os
import shutil
import stat
import sys
from pathlib import Path

from . import convert
from .core import _parse_context_txt


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
        script = bindir / "laudo-dev.ps1"
        content = f"& uv run --project {project_root} laudo @args\n"
        script.write_text(content.lstrip())
        print(f"Installed laudo wrapper at {script}")
        path_sep = ";"
        path_hint = f"$env:Path = \"{bindir};$env:Path\""
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
            print("Add this to your PowerShell profile:")
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


def _cmd_gen(dir_: Path | None, debug: Path | bool, pdf: bool, output: Path | None, template: Path | None) -> None:
    if dir_ is not None:
        os.chdir(str(dir_))
    folder = Path.cwd()
    if output is None:
        output = folder / ("laudo.pdf" if pdf else "laudo.docx")
    result = convert(folder, output, debug=debug, template=template)
    print(f"Generated: {result}")


def _cmd_captions(dir_: Path | None) -> None:
    if dir_ is not None:
        os.chdir(str(dir_))
    from .gui import run as run_gui

    run_gui(Path.cwd())


def _cmd_template(dir_: Path | None, name: str) -> None:
    if dir_ is not None:
        os.chdir(str(dir_))
    folder = Path.cwd()
    laudo_dir = folder / ".laudo"
    laudo_dir.mkdir(parents=True, exist_ok=True)
    template_file = laudo_dir / ".template"
    template_file.write_text(f"{name}\n", encoding="utf-8")
    print(f"Template '{name}' set for {folder}")


def _cmd_vars(dir_: Path | None) -> None:
    if dir_ is not None:
        os.chdir(str(dir_))
    folder = Path.cwd()
    ctx = _parse_context_txt(folder)
    print(json.dumps(ctx, indent=2, ensure_ascii=False))


def _cmd_init(dir_: Path | None, name: str) -> None:
    if dir_ is not None:
        os.chdir(str(dir_))
    folder = Path.cwd()

    laudo_dir = folder / ".laudo"
    laudo_dir.mkdir(parents=True, exist_ok=True)
    template_file = laudo_dir / ".template"
    template_file.write_text(f"{name}\n", encoding="utf-8")
    print(f"Template '{name}' set for {folder}")

    templates_dir = os.environ.get("LAUDOS_TEMPLATES_FOLDER")
    if not templates_dir:
        print("LAUDOS_TEMPLATES_FOLDER not set, skipping file copy")
        return

    src = Path(templates_dir) / name
    if not src.is_dir():
        print(f"Template folder not found: {src}, skipping file copy")
        return

    skip_exts = {".docx", ".odt"}
    copied = 0
    for item in src.iterdir():
        if item.is_file() and item.suffix not in skip_exts:
            dest = folder / item.name
            shutil.copy2(str(item), str(dest))
            copied += 1

    print(f"Copied {copied} file(s) from {src} to {folder}")


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
    gen_p.add_argument("--template", type=Path, default=None, help="Path to template file (default: template.docx or template.odt in project folder)")

    cap_p = sub.add_parser("captions", help="Open the caption editor GUI.")
    cap_p.add_argument("--dir", type=_existing_dir, default=None, help="Working directory (default: current directory)")

    tpl_p = sub.add_parser("template", help="Set the template name for the current folder (creates .template file).")
    tpl_p.add_argument("name", help="Template name (without extension)")
    tpl_p.add_argument("--dir", type=_existing_dir, default=None, help="Working directory (default: current directory)")

    vars_p = sub.add_parser("vars", help="Print context.txt variables as JSON.")
    vars_p.add_argument("--dir", type=_existing_dir, default=None, help="Working directory (default: current directory)")

    init_p = sub.add_parser("init", help="Initialize project from a template: saves template name and copies template files.")
    init_p.add_argument("name", help="Template name (without extension)")
    init_p.add_argument("--dir", type=_existing_dir, default=None, help="Working directory (default: current directory)")

    sub.add_parser("install", help="Install the laudo wrapper script to ~/.local/bin.")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    match args.command:
        case "install":
            _cmd_install()
        case "gen":
            _cmd_gen(args.dir, args.debug, args.pdf, args.output, args.template)
        case "captions":
            _cmd_captions(args.dir)
        case "template":
            _cmd_template(args.dir, args.name)
        case "vars":
            _cmd_vars(args.dir)
        case "init":
            _cmd_init(args.dir, args.name)


if __name__ == "__main__":
    main()
