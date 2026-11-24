# laudo

Write your report in **Markdown**, put your photos in a folder, and get a finished **Word (.docx)** or **PDF** document built from a template.

## Installation

You need **Python 3.13+** and **pipx** ([how to install pipx](https://github.com/renatormc/docmd/blob/main/docs/install-pipx.md)). Then run:

```bash
pipx install laudo
```

For PDF output, also install [LibreOffice](https://www.libreoffice.org/download/).

To update later: `pipx upgrade laudo`

## Quick start

1. Create a folder for your report:

   ```
   my_report/
   ├── template.docx    # the Word template
   ├── context.txt      # (optional) variables
   ├── laudo.md         # your text
   └── fotos/           # your photos
   ```

2. Open the program inside that folder:

   ```bash
   cd my_report
   laudo
   ```

3. In the window:
   - **Legendas** — write a caption for each photo.
   - **Gerar laudo** — creates `laudo.docx` (tick **PDF** to get `laudo.pdf`).

Prefer the terminal? `laudo gen` creates `laudo.docx`, and `laudo gen --pdf` creates `laudo.pdf`.

## Writing the report

### Text (`.md` files)

Write normally in Markdown: `# Title`, `## Subtitle`, `**bold**`, `*italic*` and `- lists`.

Each `.md` file becomes a variable in the template with the file's name. For example, `laudo.md` is inserted where the template has `{{p laudo|markdown }}`.

### Variables (`context.txt`)

One variable per line:

```
requisitante = Delegacia de Anápolis
data_pericia = 15/10/2026
```

Use them in the template or in the text as `{{ requisitante }}`.

### Photos

Put the photos in `fotos/`. Subfolders become groups (e.g. `fotos/local/`).

Inside the text:

| You write | Result |
|---|---|
| `image(foto1)` | inserts the photo `foto1.jpg` with its caption |
| `image_group(local, 3)` | inserts every photo in `fotos/local/`, 3 per row (any number works) |
| `${foto1}` | the number of that photo, e.g. "Conforme Foto ${foto1}" → "Conforme Foto 3" |

- Write `image(...)` and `image_group(...)` **alone on their own line** (otherwise generation stops and shows the line to fix).
- Photos are numbered automatically in the order they appear in the document.
- `${foto1}` only works if that photo was inserted with `image` or `image_group`; otherwise generation stops with an error.

### Shared templates (optional)

If you keep your templates in one folder (one subfolder per template, each with its own `template.docx`), set the `LAUDOS_TEMPLATES_FOLDER` environment variable to that folder. Then, inside a report folder, run:

```bash
laudo init <template-name>
```

## Other commands

| Command | What it does |
|---|---|
| `laudo` | opens the main window |
| `laudo gen [--pdf]` | generates the report |
| `laudo captions` | opens only the caption editor |
| `laudo reduce-images fotos fotos` | shrinks large photos (you pick the maximum size). **Overwrites the originals**: use another destination folder to keep them |
| `laudo --help` | lists every command and option |

## Full documentation

The [user guide](https://github.com/renatormc/docmd/blob/main/docs/user-guide.md) covers everything else: sections inside `.md` files, `.json` data, photo groups in the template, numbering tables and figures, shared templates, and the full list of filters and functions.

## License

MIT
