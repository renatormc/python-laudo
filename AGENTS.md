# laudo

Convert markdown files to **docx** or **pdf** using `docxtpl` templates and LibreOffice headless.

## Architecture

```
src/laudo/
├── __init__.py          # Public API: convert()
├── __main__.py          # CLI entry point (click)
├── core.py              # Core conversion logic
├── db.py                # SQLite caption storage
├── assets.py            # Asset (image) handling
├── exif.py              # EXIF caption read/write (legacy)
├── images.py            # Image listing, thumbnails, reduced
├── filters/             # Custom Jinja2 filters (markdown, etc.)
├── globals/             # Jinja2 globals (subdoc)
├── gui/                 # PySide6 caption editor
└── pdf.py               # PDF export via LibreOffice
```

## Public API

```python
def convert(
    folder: str | Path,   # Folder containing the project files
    output: str | Path,   # Output path — use .docx or .pdf extension
) -> Path
```

## Input Folder Structure

The `folder` parameter must contain:

```
my_project/
├── template.docx          # (optional) docxtpl template with Jinja2 placeholders
├── .laudo/                # (created automatically)
│   ├── .template          # (optional) file containing template name (without extension)
│   ├── pics.sqlite        # Image captions database
│   └── thumbs/            # Generated thumbnails and reduced images
├── fotos/                 # Images with captions (stored in SQLite)
│   ├── image1.png
│   └── image2.jpg
├── context.txt            # (optional) Variables one per line: varname = value
├── intro.md               # One or more .md files
└── chapter-1.md
```

## Template Resolution

Templates are resolved in the following order:

1. **Working folder**: Looks for `template.docx` or `template.odt` in the project folder.
2. **`.template` file**: If not found, reads the `.template` file in the `.laudo/` folder. The file should contain the template name (without extension).
3. **`LAUDOS_TEMPLATES_FOLDER`**: If `.template` exists, looks for the template in the directory specified by the `LAUDOS_TEMPLATES_FOLDER` environment variable. The template file must be named `<name>.docx` or `<name>.odt`.

Example `.template` file:
```
my-report-template
```

This would look for `my-report-template.docx` or `my-report-template.odt` in `$LAUDOS_TEMPLATES_FOLDER`.

## Context Building

All data below is merged and passed to `docxtpl.DocxTemplate.render()`:

### From `context.txt`
- Format: `varname = value` (one per line)
- Lines starting with `#`, empty lines, and lines without `=` are skipped.
- Parsed first so its variables are available for substitution in markdown files.

### From markdown files
- Every `.md` file is read and its content is processed through Jinja2 with the variables from `context.txt`.
- This means you can use `{{ varname }}` inside `.md` files to reference values from `context.txt`.
- After substitution, the result is added to the context.
- The variable name is the filename without extension, with whitespace replaced by underscores.
- Example: `intro.md` → context key `intro`, `chapter 1.md` → context key `chapter_1`.

### From fotos folder
- All image files inside `fotos/` are listed.
- A context variable `pics` is created as a `dict[str, dict]`.
- Key: filename without extension. Value: `{"path": Path, "caption": str, "thumb": Path, "reduced": Path}`.
- `caption` is read from the SQLite database `pics.sqlite` in the `.laudo/` folder via `db.py`.
- `thumb` and `reduced` are generated on demand via `images.py` and stored in `.laudo/thumbs/`.

### `subdoc` global function

- A Jinja2 global named `subdoc` is registered in the docxtpl environment.
- Pass the relative path (relative to `assets/`) as the argument.
- The returned subdocument can be inserted into the template using docxtpl's subdocument syntax (e.g., `{{p subdoc("cover.docx") }}`).

### `markdown` Jinja2 filter
- A custom filter named `markdown` is registered in the docxtpl environment.
- For now it simply returns the raw markdown text unchanged.
- Future: it will parse markdown and return proper docx elements (paragraphs, headings, lists, images, etc.).

Example template usage:

```jinja2
{{p intro|markdown }}
```

## CLI (`__main__.py`)

Uses **click**:

```bash
laudo [command] [options]
```

- `gen [--dir <folder>] [--debug]` — generate docx/pdf from markdown files (default: current directory).
- `captions [--dir <folder>]` — open the caption editor (PySide6).
- `template <name> [--dir <folder>]` — set the template name for a folder (creates `.laudo/.template` file).
- `install` — install the `laudo` wrapper script to `~/.local/bin/`.

## GUI (`gui/`)

A PySide6 caption editor that displays all images from `fotos/` as thumbnails with a text field for each caption. Captions are saved to the SQLite database `pics.sqlite` in the `.laudo/` folder via `db.py`.

## Conventions

- Type hints everywhere, no `Any` unless strictly necessary.
- Use `pathlib.Path` for all file paths.
- Use `docxtpl.DocxTemplate` for template rendering.
- Use `subprocess.run(["libreoffice", "--headless", "--convert-to", "pdf", ...])` for pdf conversion.
- Business logic in `core.py`, I/O and assets in `assets.py`, pdf conversion in `pdf.py`.
- Main function `convert()` lives in `__init__.py` as the public entry point.

## Dependencies

- `docxtpl` — Jinja2-based docx template engine
- `python-magic` (optional) — MIME type detection for assets
- LibreOffice installed system-wide for PDF conversion

## Commands

- `uv run laudo gen` — run the CLI
- `uv run laudo captions` — open the caption editor
- `uv add <pkg>` — add a dependency
- `uv sync` — sync environment
- `uv run pytest` — run all tests
- `uv run pytest -v` — run tests verbosely

## Publishing to PyPI

1. Create an API token at https://pypi.org/manage/account/token/
2. Set it permanently on Windows (run once in PowerShell):

```powershell
[System.Environment]::SetEnvironmentVariable("UV_PUBLISH_TOKEN", "pypi-...", "User")
```

Replace `pypi-...` with your actual token. Restart PowerShell afterwards.
To publish, run:

```powershell
.\dev.ps1 publish
```
