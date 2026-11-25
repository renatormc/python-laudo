# laudo

Escreva o laudo em **Markdown**, coloque as fotos numa pasta e receba um documento **Word (.docx)** ou **PDF** pronto, montado a partir de um modelo.

## Instalação

Você precisa do **Python 3.13+** e do **pipx** ([como instalar o pipx](https://github.com/renatormc/python-laudo/blob/main/docs/install-pipx.md)). Depois, execute:

```bash
pipx install laudo
```

Para gerar PDF, instale também o [LibreOffice](https://pt-br.libreoffice.org/baixe-ja/libreoffice-novo/).

Para atualizar depois: `pipx upgrade laudo`

## Primeiros passos

1. Crie uma pasta para o laudo:

   ```
   meu_laudo/
   ├── template.docx    # o modelo do Word
   ├── context.txt      # (opcional) variáveis
   ├── laudo.md         # o seu texto
   └── fotos/           # as suas fotos
   ```

2. Abra o programa dentro dessa pasta:

   ```bash
   cd meu_laudo
   laudo
   ```

3. Na janela:
   - **Legendas** — escreva uma legenda para cada foto.
   - **Gerar laudo** — cria o `laudo.docx` (marque **PDF** para gerar `laudo.pdf`).

Prefere o terminal? `laudo gen` cria o `laudo.docx`, e `laudo gen --pdf` cria o `laudo.pdf`.

## Escrevendo o laudo

### Texto (arquivos `.md`)

Escreva normalmente em Markdown: `# Título`, `## Subtítulo`, `**negrito**`, `*itálico*` e `- listas`.

Cada arquivo `.md` vira uma variável no modelo, com o nome do arquivo. Por exemplo, o `laudo.md` é inserido onde o modelo tiver `{{p laudo|markdown }}`.

### Variáveis (`context.txt`)

Uma variável por linha:

```
requisitante = Delegacia de Anápolis
data_pericia = 15/10/2026
```

Use-as no modelo ou no texto como `{{ requisitante }}`.

### Fotos

Coloque as fotos em `fotos/`. Subpastas viram grupos (por exemplo, `fotos/local/`).

Dentro do texto:

| Você escreve | Resultado |
|---|---|
| `image(foto1)` | insere a foto `foto1.jpg` com a legenda |
| `image_group(local, 3)` | insere todas as fotos de `fotos/local/`, 3 por linha (qualquer número de colunas funciona) |
| `${foto1}` | o número dessa foto, ex.: "Conforme Foto ${foto1}" → "Conforme Foto 3" |

- Escreva `image(...)` e `image_group(...)` **sozinhos na linha** (caso contrário, a geração para e mostra a linha a corrigir).
- As fotos são numeradas automaticamente na ordem em que aparecem no documento.
- `${foto1}` só funciona se a foto tiver sido inserida com `image` ou `image_group`; caso contrário, a geração para com um erro.

### Modelos compartilhados (opcional)

Se você guarda os modelos numa pasta (uma subpasta por modelo, cada uma com seu `template.docx`), aponte a variável de ambiente `LAUDOS_TEMPLATES_FOLDER` para essa pasta. Depois, dentro da pasta do laudo, execute:

```bash
laudo init <nome-do-modelo>
```

## Outros comandos

| Comando | O que faz |
|---|---|
| `laudo` | abre a janela principal |
| `laudo gen [--pdf]` | gera o laudo |
| `laudo captions` | abre só o editor de legendas |
| `laudo reduce-images fotos fotos` | reduz fotos grandes (você escolhe o tamanho máximo). **Sobrescreve os originais**: use outra pasta de destino para preservá-los |
| `laudo --help` | lista todos os comandos e opções |

## Documentação completa

O [guia do usuário](https://github.com/renatormc/python-laudo/blob/main/docs/user-guide.md) cobre todo o resto: seções dentro dos arquivos `.md`, dados em `.json`, grupos de fotos no modelo, numeração de tabelas e figuras, modelos compartilhados e a lista completa de filtros e funções.

## Licença

MIT
