# laudo

Convert markdown files to **docx** or **pdf** using `docxtpl` templates and LibreOffice headless.

## Installation

```bash
pip install laudo
```

Requires **Python 3.13+** and **LibreOffice** installed system-wide for PDF output.

## Usage

### CLI

```bash
laudo <folder> <output>
```

- `<folder>` — directory with your project files.
- `<output>` — output file (`.docx` or `.pdf`).

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
├── fotos/                 # Images with captions (EXIF)
│   ├── logo.png
│   └── photo.jpg
├── context.txt            # (optional) Variables one per line
├── intro.md               # One or more .md files
└── chapter-1.md
```

### `template.docx`

A standard Word document using [docxtpl](https://github.com/elapouya/python-docxtpl) syntax. Use Jinja2 placeholders like `{{ variable }}` or `{{p intro|markdown }}`.

### `context.txt`

Optional file with variables in `key = value` format, one per line:

```
author = John Doe
title = My Document
```

Lines starting with `#` and empty lines are ignored.

These variables are also available for substitution inside your `.md` files (see below).

### Markdown files

Every `.md` file is read and its content is injected into the template context. The variable name is the filename without extension (whitespace replaced by underscores):

| File | Context key |
|---|---|
| `intro.md` | `intro` |
| `chapter 1.md` | `chapter_1` |

You can use `{{ varname }}` inside `.md` files to reference values from `context.txt`:

**context.txt:**
```
name = John Doe
```

**intro.md:**
```markdown
# Hello {{ name }}
```

The result will be `# Hello John Doe`, then stored in context key `intro`.

#### `image_group(name, cols)` shorthand

Inside `.md` files you can use the `image_group(name, cols)` shorthand to embed a sub-template with images from a specific photo group:

```markdown
image_group(events, 3)
```

This is automatically expanded to:

```jinja2
{{p subdoc('image_group', pics=pics.group('events'), cols=3) }}
```

It renders the `image_group.docx` sub-template, passing the images from the `events` group and the number of columns. See [Fotos](#fotos) for how image groups work.

Use the `subdoc` global function to embed `.docx` sub-templates located alongside the main template:

```jinja2
{{p subdoc("cover.docx") }}
```

You can also pass context variables to the sub-template:

```jinja2
{{p subdoc("cover.docx", title=title, author=author) }}
```

Use the `markdown` filter in your template:

```jinja2
{{p intro|markdown }}
```

### Fotos

All image files inside `fotos/` are listed recursively (including subdirectories). Two context variables are injected:

- `pics` — `list[dict]` of all images
- `pics_map` — `dict[str, dict]` keyed by `refname` for quick lookup

Each image dict:

```json
{
  "refname": "logo",
  "path": "fotos/logo.png",
  "caption": "",
  "thumb": ".laudo/thumbs/logo_thumb.jpg",
  "reduced": ".laudo/thumbs/logo_reduced.jpg",
  "label": "Foto",
  "group": ""
}
```

- `refname` is the filename without extension.
- `group` is empty for images directly in `fotos/`, or the subfolder path (e.g. `"events"`, `"events/party"`) for images in subdirectories.
- Results are sorted first by `group`, then by `refname`.
- Captions are read from the SQLite database `pics.sqlite` in `.laudo/`.
- Thumbnails and reduced images are generated on demand and stored in `.laudo/thumbs/`.

## PDF Output

When the output path ends with `.pdf`, a docx is generated first and then converted to PDF via LibreOffice headless:

```bash
laudo my_project/ output.pdf
```

The intermediate docx file is automatically removed.

## License

MIT
