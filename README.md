# laudo

Convert markdown files to **docx** or **pdf** using `docxtpl` templates.

## Installation

```bash
pip install laudo
```

Requires **Python 3.13+** and **LibreOffice** for PDF output.

## Usage

### CLI

```bash
laudo gen [--dir <folder>] [--debug] [--pdf] [--output <path>] [--template <path>]
laudo captions [--dir <folder>]
laudo template <name> [--dir <folder>]
laudo vars [--dir <folder>]
laudo init <name> [--dir <folder>]
laudo install
```

### Python API

```python
from laudo import convert

convert("my_project/", "output.docx")
convert("my_project/", "output.pdf")
```

## Input Folder Structure

```
my_project/
├── template.docx          # docxtpl template with Jinja2 placeholders
├── fotos/                 # Images (captions edited via GUI)
│   ├── image1.png
│   └── events/
│       └── party.jpg
├── context.txt            # (optional) Variables one per line: key = value
├── intro.md               # One or more .md files
└── chapter-1.md
```

### Template

A standard Word document using [docxtpl](https://github.com/elapouya/python-docxtpl) syntax with Jinja2 placeholders like `{{ variable }}` or `{{p intro|markdown }}`.

To use a template from a shared folder, create `.laudo/.template` with the template name and set the `LAUDOS_TEMPLATES_FOLDER` environment variable.

### context.txt

Optional file with variables in `key = value` format, one per line. Lines starting with `#` and empty lines are ignored. These variables are available for substitution inside `.md` files via `{{ varname }}`.

### Markdown files

Every `.md` file is read and its content is injected as a template variable named after the filename (without extension, spaces → underscores):

| File | Template variable |
|---|---|
| `intro.md` | `intro` |
| `chapter 1.md` | `chapter_1` |

Inside markdown files you can reference context variables with `{{ varname }}` and embed image groups with `image_group(name, cols)`.

### Images

All images in `fotos/` (including subdirectories) are available as the `pics` variable in templates. Use `pics.group("events")` to get images from a subfolder, or `pics.all` for all images. Captions are edited via the `laudo captions` GUI.

### Template helpers

- `{{p variable\|markdown }}` — render markdown as formatted docx content
- `{{p subdoc("file.docx", key=val) }}` — embed a sub-template
- `{{p image("fotos/logo.png", width=50) }}` — inline image with size control

## License

MIT
