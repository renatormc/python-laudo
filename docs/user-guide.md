# laudo — User guide

Everything you can do with laudo, from the folder layout to every filter available in templates.

- [How it works](#how-it-works)
- [Project folder](#project-folder)
- [The main window](#the-main-window)
- [Caption editor](#caption-editor)
- [Writing the text (`.md`)](#writing-the-text-md)
- [Variables](#variables)
- [Photos](#photos)
- [Automatic numbering (`${...}`)](#automatic-numbering-)
- [Templates](#templates)
- [Filters](#filters)
- [Functions](#functions)
- [Command line](#command-line)
- [Troubleshooting](#troubleshooting)

---

## How it works

1. laudo reads your project folder: variables, text files (`.md`) and photos.
2. It fills a Word template (`template.docx`) with that content.
3. It numbers photos and references (`Foto 1`, `Foto 2`…).
4. It saves `laudo.docx`, or `laudo.pdf` (PDF needs LibreOffice).

## Project folder

```
my_report/
├── template.docx        # Word template (see "Templates")
├── context.txt          # variables: name = value
├── dados.json           # (optional) structured data
├── laudo.md             # your text (one or more .md files)
├── fotos/               # photos; subfolders become groups
│   ├── porta.jpg
│   └── local/
│       ├── sala.jpg
│       └── cozinha.jpg
└── .laudo/              # created automatically: captions and image cache
```

- If a `context/` subfolder exists, `context.txt`, `.json` and `.md` files are read **from it** instead of the project folder.
- `.laudo/` holds the captions (`pics.sqlite`) and the reduced copies of the photos (`thumbs/`). Don't delete it unless you want to lose the captions.

## The main window

Run `laudo` inside the project folder (or choose the folder with **Selecionar…**).

| Button | What it does |
|---|---|
| **Gerar laudo** | creates `laudo.docx` in the folder. Tick **PDF** to create `laudo.pdf` instead |
| **Legendas** | opens the caption editor |
| **Variáveis** | shows the variables read from `context.txt` |
| **Contexto** | shows **everything** available to the template (variables, texts, photos). Useful to find a variable's exact name |
| **Reduzir imagens** | shrinks large images in a folder, or inside a `.docx`/`.odt` |

Tasks run in the background. If something fails, a dialog shows the error and its details.

## Caption editor

Opened with **Legendas** (or `laudo captions`).

- Shows every photo in `fotos/` with a caption field.
- The search box filters by file name or caption.
- Click a photo to see it large. In that view:
  - **Anterior / Próxima** navigate between photos.
  - **Enter** keeps the caption, copies it to the clipboard and moves to the next photo.
- Click **Salvar** to store the captions. Closing without saving discards the changes.

The caption appears next to the photo in the report as `Foto 3 - <caption>`.

## Writing the text (`.md`)

Each `.md` file becomes a variable named after the file (spaces become `_`):

| File | Variable |
|---|---|
| `laudo.md` | `laudo` |
| `exame local.md` | `exame_local` |

In the template, insert it with `{{p laudo|markdown }}`.

### Supported formatting

| You write | Result |
|---|---|
| `# Title` | heading level 1 (also `##` and `###`) |
| `**text**` | **bold** |
| `*text*` | *italic* |
| `- item` | bullet list item |
| blank line | ignored (each line is its own paragraph) |

Headings use the template's heading styles, so numbering and fonts come from the template.

### Sections inside one file

A single `.md` can feed several variables. Start each part with `[[name]]`:

```
[[historico]]
Text of the history…

[[conclusao]]
Text of the conclusion…
```

This creates the variables `historico` and `conclusao` (the file-name variable is **not** created in this case).

### Variables inside the text

Write `{{ variable }}` to use any variable from `context.txt` or from a `.json` file:

```
The examination started at {{ inicio_pericia }}.
```

Inside `.md` files you can use Jinja's built-in filters (`{{ nome|upper }}`), but **not** the laudo [filters](#filters). Those only work in the template.

## Variables

### `context.txt`

```
# lines starting with # are comments
requisitante = Delegacia de Anápolis
data_pericia = 15/10/2026
cols = 2
```

- One `name = value` per line. Lines without `=` are ignored.
- Every value is **text**. Use a filter when you need a date or a number: `{{ data_pericia|data_simples }}`, `{{ cols|int }}`.

### `.json` files

Each `.json` file becomes a variable named after the file. With `pessoas.json`:

```json
[{"nome": "João", "gender": "M"}, {"nome": "Maria", "gender": "F"}]
```

you can write `{% for p in pessoas %}{{ p.nome }}{% endfor %}` in the template.

## Photos

Put the images (`.jpg`, `.jpeg`, `.png`, `.tif`, `.tiff`, `.webp`) in `fotos/`. Subfolders become **groups**: the photos in `fotos/local/` belong to the group `local`.

The **name** of a photo is its file name without the extension: `fotos/local/sala.jpg` → `sala`. Names must be unique, even across subfolders.

Large photos are inserted as reduced copies (at most 450 px). Your originals are never changed.

### In the text (`.md`)

| You write | Result |
|---|---|
| `image(sala)` | the photo `sala` with its caption |
| `image_group(local, 2)` | every photo of the group `local`, 2 per row (any number of columns works) |
| `image_group(local, cols)` | number of columns taken from a variable |

Write these **alone on their own line**. Otherwise generation stops and shows the line to fix.

### In the template

The variable `pics` gives access to every photo:

| Expression | Result |
|---|---|
| `pics.all()` | list of all photos |
| `pics.group("local")` | photos of one group (empty list if none) |
| `pics.get("sala")` | one photo, or nothing if it doesn't exist |
| `pics.require("sala")` / `pics.require_group("local")` | same, but stops with a clear error if missing |
| `{% if pics %}` | true when there is at least one photo |

Each photo has: `refname` (name), `caption`, `group`, `label` (`"Foto"`), `path` (original file), `reduced` (copy used in the document) and `thumb` (thumbnail).

To insert a photo grid directly in the template:

```
{{p subdoc("image_group", pics=pics.group("anexo"), cols=2) }}
```

`image_group` also accepts `image_width=<mm>` to force the width of every photo.

To hide a photo from a list, start its name with `_` and use the `filter_dashes` function: `filter_dashes(pics.all(), "refname")`.

## Automatic numbering (`${...}`)

Every photo inserted with `image`, `image_group` or `caption(...)` gets a number, in the order it appears in the document: `Foto 1`, `Foto 2`…

To mention a photo in the text, write its name between `${ }`:

```
As shown in Foto ${sala}, the door was open.
```

→ "As shown in Foto 3, the door was open."

You can number other things the same way. Write `${Label|name}` where the item appears and `${name}` where you mention it:

```
${Tabela|valores} Values found
…
see table ${valores}
```

→ "Tabela 1 Values found … see table 1". Each label (`Foto`, `Tabela`, `Figura`…) has its own sequence.

Generation stops with an error when:

- a `${name}` refers to something that was never inserted, or
- the same `${Label|name}` appears twice.

`laudo gen --pos-edit` skips this step and leaves the `${...}` markers in the document.

## Templates

The template is a normal Word document with placeholders ([docxtpl](https://docxtpl.readthedocs.io/) / Jinja2 syntax):

| Syntax | Use |
|---|---|
| `{{ variable }}` | inserts a value |
| `{{ variable\|filter }}` | inserts a value transformed by a [filter](#filters) |
| `{{p laudo\|markdown }}` | inserts a `.md` text as formatted paragraphs (must be alone in the paragraph) |
| `{%p if condition %}` … `{%p endif %}` | shows paragraphs only when the condition is true |
| `{%p for item in list %}` … `{%p endfor %}` | repeats paragraphs for every item |
| `{%tr for … %}` / `{%tc for … %}` | repeats table rows / columns |
| `{{p subdoc("name", var=value) }}` | inserts another `.docx` (see below) |
| `{{ image(path, width=50) }}` | inserts an image |

### Which template is used

1. `template.docx` in the project folder; otherwise
2. the template named in `.laudo/.template`, looked up in `$LAUDOS_TEMPLATES_FOLDER/<name>/template.docx`.

`laudo gen --template <file>` uses a specific file instead.

### Shared templates

Keep a folder with one subfolder per template, and point the `LAUDOS_TEMPLATES_FOLDER` environment variable to it:

```
templates/
└── local-de-crime/
    ├── template.docx
    ├── context.txt      # copied into new projects
    └── laudo.md         # copied into new projects
```

In a new, empty project folder, `laudo init local-de-crime` selects the template and copies its other files (everything except `.docx`) into the project. `laudo template <name>` only selects the template, without copying anything.

### Sub-documents (`subdoc`)

`{{p subdoc("capa") }}` inserts `capa.docx`. It is looked up in the project folder, then in the shared template folder, then among the templates built into laudo (`image_group`).

Pass values to the sub-document: `{{p subdoc("capa", titulo=nome_exame) }}`. Inside `capa.docx`, use `{{ titulo }}`.

### Images in the template

`{{ image(path, width=50) }}` inserts an image. The sizes are in **millimetres**.

- Give `width` **or** `height`, not both.
- `max_height` / `max_width` limit the other side: `image(p.reduced, 150, max_height=220)`.
- The file must exist. If it doesn't, the text `None` appears in its place.

## Filters

Use them in the template as `{{ value|filter }}`, or with arguments as `{{ value|filter(arg) }}`. All of Jinja's [built-in filters](https://jinja.palletsprojects.com/en/stable/templates/#list-of-builtin-filters) (`upper`, `lower`, `title`, `default`, `int`, `join`, `length`, `replace`…) also work.

### Text

| Filter | Example | Result |
|---|---|---|
| `markdown` | `{{p laudo\|markdown }}` | `.md` text as formatted paragraphs |
| `not_null` | `{{ x\|not_null }}` | `""` when the value is empty (None) |
| `xxx` | `{{ x\|xxx }}` | `XXX` when the value is empty (None) |
| `str` | `{{ 12\|str }}` | converts to text |
| `file_stem` | `{{ "fotos/a.jpg"\|file_stem }}` | `a` |
| `join_enumerate` | `{{ ["a","b","c"]\|join_enumerate }}` | `a, b e c` |
| | `{{ ["a","b"]\|join_enumerate(true) }}` | `"a" e "b"` |
| `br` | `{{ item\|br(loop) }}` inside a `for` | adds a line break before every item except the first |
| `is_male` | `{{ "João Silva"\|is_male }}` | `True` when the first name ends in "o" |

### Dates

| Filter | Example | Result |
|---|---|---|
| `data_simples` | `{{ "2026-10-15"\|data_simples }}` | `15/10/2026` |
| `data_mes_extenso` | `{{ "15/10/2026"\|data_mes_extenso }}` | `15 de outubro de 2026` (day 1 → `1°`) |
| `datetime` | `{{ "15/10/2026"\|datetime }}` | converts `dd/mm/yyyy` text to a date |
| `data_completa` | `{{ "15/10/2026"\|datetime\|data_completa }}` | `15 (quinze) dias do mês de outubro do ano de 2026 (dois mil e vinte e seis)` |
| `dia` | `{{ d\|dia }}` | `15` |
| `dia_extenso` | `{{ d\|dia_extenso }}` | `15 (quinze)` |
| `mes_extenso` | `{{ d\|mes_extenso }}` | `outubro` |
| `hora_minuto` | `{{ d\|hora_minuto }}` | `14:05` |
| `ornow` | `{{ data_laudo\|ornow\|data_mes_extenso }}` | the value, or **today** when it is empty |

`data_simples` and `data_mes_extenso` accept text (`15/10/2026` or `2026-10-15`). `data_completa`, `dia`, `dia_extenso`, `mes_extenso` and `hora_minuto` need a date: convert text first with `|datetime`. Otherwise they return an empty text or `XXX`.

### Numbers and money

| Filter | Example | Result |
|---|---|---|
| `numero_extenso_masc` | `{{ 1234\|numero_extenso_masc }}` | `um mil, duzentos e trinta e quatro` |
| `numero_extenso_fem` | `{{ 2\|numero_extenso_fem }}` | `duas` |
| `get_extenso` | `{{ 200\|get_extenso(true) }}` | `duzentas` (`true` = feminine) |
| `moeda_extenso` | `{{ 10.5\|moeda_extenso }}` | `R$ 10,50 (dez reais e cinquenta centavos)` |

`moeda_extenso` needs a number: use `{{ valor|float|moeda_extenso }}` for values from `context.txt`.

### Case numbers (`rg/ano`)

| Filter | Example | Result |
|---|---|---|
| `perrg` | `{{ "1234/2026"\|perrg }}` | `1234` |
| `perano` | `{{ "1234/2026"\|perano }}` | `2026` |
| `rgano` | `{{ "1234/2026"\|rgano }}` | `{'rg': 1234, 'ano': 2026}` |

## Functions

Call them in the template as `{{ function(arguments) }}`.

### Lists

| Function | Example | Result |
|---|---|---|
| `str_list` | `str_list(relatores, revisores)` | splits texts separated by `, ` into one list, ignoring empty values: `"a, b"`, `"c"` → `['a', 'b', 'c']` |
| `to_table` | `to_table(pics.all(), 3)` | splits a list into rows of 3 (for grids) |
| `len` | `len(peritos)` | number of items |
| `join_lists` | `join_lists(a, b)` | joins lists |
| `remove_nulls` | `remove_nulls(items, "campo")` | removes empty items and items whose `campo` is empty |
| `filter_dashes` | `filter_dashes(pics.all(), "refname")` | removes items whose field starts with `_` |
| `count_qtd` | `count_qtd(itens, "qtd")` | sum of the `qtd` field (or of the numbers in the list) |
| `get_paragraphs` | `get_paragraphs(texto)` | splits a text into lines |

### Gender and plural

| Function | Example | Result |
|---|---|---|
| `plural` | `plural("perito", 2)` | `peritos` (adds `s` when the number is > 1) |
| `ifplural` | `ifplural(peritos, "s")` | `s` when the list has more than one item; the 3rd argument is the singular form (default empty) |
| `gender` | `gender(pessoa, "perito")` | `perita` when `pessoa.gender` is `"F"` |
| `male_female` | `male_female(pessoa, "o", "a")` | `"o"` or `"a"` according to `pessoa.gender` (`"M"`/`"F"`) |

### Other

| Function | Example | Result |
|---|---|---|
| `not_null_or` | `not_null_or(x, "não informado")` | `x`, or the default when `x` is empty |
| `case_` | `case_(tipo, {"a": "Arma", "default": "Outro"})` | value for the key, or `default` |
| `caption` | `caption("Foto", p.refname, p.caption)` | `${Foto\|sala} - caption` (numbered later) |
| `join_path` | `join_path("fotos", "a.jpg")` | joins path parts |
| `subdoc`, `image` | see [Templates](#templates) | |

## Command line

All commands accept `--dir <folder>` to work on another folder (default: the current one).

| Command | What it does |
|---|---|
| `laudo` / `laudo gui` | opens the main window |
| `laudo gen` | creates `laudo.docx` |
| `laudo gen --pdf` | creates `laudo.pdf` |
| `laudo gen --output <file>` | chooses the output file |
| `laudo gen --template <file>` | uses another template |
| `laudo gen --debug [file]` | prints everything passed to the template (or saves it to a file) |
| `laudo gen --pos-edit` | keeps the `${...}` markers without numbering them |
| `laudo captions` | opens the caption editor |
| `laudo vars` | prints the variables of `context.txt` |
| `laudo context [file]` | prints (or saves) everything available to the template, as JSON |
| `laudo init <name>` | starts a project from a shared template |
| `laudo template <name>` | selects a shared template for the folder |
| `laudo reduce-images <source> <dest> [--max N]` | shrinks images: folder → folder, or inside a `.docx`/`.odt`. Without `--max`, asks the size (default 450 px). If `dest` is the same as `source`, the originals are overwritten |

## Troubleshooting

| Message | What to do |
|---|---|
| `Imagem 'x' … não encontrada na pasta fotos/` | check the name in `image(x)` against the file names (the message lists the available ones) |
| `Grupo de imagens 'x' … não encontrado` | create `fotos/x/` with photos, or fix the group name |
| `Uso inválido de image/image_group na linha …` | put the command alone on its own line, with the number of columns for `image_group` |
| `Referência "x" não encontrada` | `${x}` mentions a photo or item that was not inserted in the document |
| `Referência "…" … está duplicada` | the same item (`${Label\|name}`) was inserted twice |
| `Template 'x.docx' não encontrado` | the message lists every folder searched; add the file or fix `.laudo/.template` |
| `No filter named '…'` | that filter does not exist, or a laudo filter was used inside a `.md` file (only allowed in the template) |
| A variable appears empty | open **Contexto** and check the exact variable name |
