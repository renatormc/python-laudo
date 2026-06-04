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

All image files inside `fotos/` are listed in the `pics` context variable:

```json
{
  "logo": {"path": "fotos/logo.png", "caption": "", "thumb": "fotos/.thumbs/logo_thumb.jpg", "reduced": "fotos/.thumbs/logo_reduced.jpg"},
  "photo": {"path": "fotos/photo.jpg", "caption": "", "thumb": "fotos/.thumbs/photo_thumb.jpg", "reduced": "fotos/.thumbs/photo_reduced.jpg"}
}
```

Captions are read from EXIF `ImageDescription` metadata.

## PDF Output

When the output path ends with `.pdf`, a docx is generated first and then converted to PDF via LibreOffice headless:

```bash
laudo my_project/ output.pdf
```

The intermediate docx file is automatically removed.

## License

MIT
