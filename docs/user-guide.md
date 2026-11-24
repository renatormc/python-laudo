# laudo — Guia do usuário

Tudo o que dá para fazer com o laudo, da estrutura da pasta a cada filtro disponível nos modelos.

- [Como funciona](#como-funciona)
- [Pasta do projeto](#pasta-do-projeto)
- [Janela principal](#janela-principal)
- [Editor de legendas](#editor-de-legendas)
- [Escrevendo o texto](#escrevendo-o-texto)
- [Variáveis](#variáveis)
- [Fotos](#fotos)
- [Numeração automática](#numeração-automática)
- [Modelos](#modelos)
- [Filtros](#filtros)
- [Funções](#funções)
- [Linha de comando](#linha-de-comando)
- [Solução de problemas](#solução-de-problemas)

---

## Como funciona

1. O laudo lê a pasta do projeto: variáveis, textos (`.md`) e fotos.
2. Preenche um modelo do Word (`template.docx`) com esse conteúdo.
3. Numera as fotos e as referências (`Foto 1`, `Foto 2`…).
4. Salva o `laudo.docx`, ou o `laudo.pdf` (o PDF precisa do LibreOffice).

## Pasta do projeto

```
meu_laudo/
├── template.docx        # modelo do Word (veja "Modelos")
├── context.txt          # variáveis: nome = valor
├── dados.json           # (opcional) dados estruturados
├── laudo.md             # o seu texto (um ou mais arquivos .md)
├── fotos/               # fotos; subpastas viram grupos
│   ├── porta.jpg
│   └── local/
│       ├── sala.jpg
│       └── cozinha.jpg
└── .laudo/              # criada automaticamente: legendas e cache de imagens
```

- Se existir uma subpasta `context/`, os arquivos `context.txt`, `.json` e `.md` são lidos **dela**, e não da pasta do projeto.
- A pasta `.laudo/` guarda as legendas (`pics.sqlite`) e as cópias reduzidas das fotos (`thumbs/`). Não a apague, a menos que queira perder as legendas.

## Janela principal

Execute `laudo` dentro da pasta do projeto (ou escolha a pasta em **Selecionar…**).

| Botão | O que faz |
|---|---|
| **Gerar laudo** | cria o `laudo.docx` na pasta. Marque **PDF** para criar o `laudo.pdf` |
| **Legendas** | abre o editor de legendas |
| **Variáveis** | mostra as variáveis lidas do `context.txt` |
| **Contexto** | mostra **tudo** o que está disponível para o modelo (variáveis, textos, fotos). Útil para descobrir o nome exato de uma variável |
| **Reduzir imagens** | reduz imagens grandes de uma pasta, ou dentro de um `.docx`/`.odt` |

As tarefas rodam em segundo plano. Se algo falhar, uma janela mostra o erro e os detalhes.

## Editor de legendas

Aberto pelo botão **Legendas** (ou por `laudo captions`).

- Mostra todas as fotos de `fotos/`, cada uma com um campo de legenda.
- A caixa de busca filtra pelo nome do arquivo ou pela legenda.
- Clique numa foto para vê-la grande. Nessa tela:
  - **Anterior / Próxima** navegam entre as fotos.
  - **Enter** guarda a legenda, copia o texto para a área de transferência e passa para a próxima foto.
- Clique em **Salvar** para gravar as legendas. Fechar sem salvar descarta as alterações.

No laudo, a legenda aparece junto da foto como `Foto 3 - <legenda>`.

## Escrevendo o texto

Cada arquivo `.md` vira uma variável com o nome do arquivo (espaços viram `_`):

| Arquivo | Variável |
|---|---|
| `laudo.md` | `laudo` |
| `exame local.md` | `exame_local` |

No modelo, insira o texto com `{{p laudo|markdown }}`.

### Formatação suportada

| Você escreve | Resultado |
|---|---|
| `# Título` | título de nível 1 (também `##` e `###`) |
| `**texto**` | **negrito** |
| `*texto*` | *itálico* |
| `- item` | item de lista com marcador |
| linha em branco | ignorada (cada linha é um parágrafo) |

Os títulos usam os estilos de título do modelo, então a numeração e as fontes vêm do modelo.

### Seções dentro de um arquivo

Um único `.md` pode alimentar várias variáveis. Comece cada parte com `[[nome]]`:

```
[[historico]]
Texto do histórico…

[[conclusao]]
Texto da conclusão…
```

Isso cria as variáveis `historico` e `conclusao` (nesse caso, a variável com o nome do arquivo **não** é criada).

### Variáveis dentro do texto

Escreva `{{ variavel }}` para usar qualquer variável do `context.txt` ou de um arquivo `.json`:

```
Os exames foram iniciados às {{ inicio_pericia }}.
```

Dentro dos arquivos `.md` você pode usar os filtros nativos do Jinja (`{{ nome|upper }}`), mas **não** os [filtros](#filtros) do laudo. Esses só funcionam no modelo.

## Variáveis

### `context.txt`

```
# linhas começando com # são comentários
requisitante = Delegacia de Anápolis
data_pericia = 15/10/2026
cols = 2
```

- Um `nome = valor` por linha. Linhas sem `=` são ignoradas.
- Todo valor é **texto**. Use um filtro quando precisar de uma data ou de um número: `{{ data_pericia|data_simples }}`, `{{ cols|int }}`.

### Arquivos `.json`

Cada arquivo `.json` vira uma variável com o nome do arquivo. Com o `pessoas.json`:

```json
[{"nome": "João", "gender": "M"}, {"nome": "Maria", "gender": "F"}]
```

você pode escrever `{% for p in pessoas %}{{ p.nome }}{% endfor %}` no modelo.

## Fotos

Coloque as imagens (`.jpg`, `.jpeg`, `.png`, `.tif`, `.tiff`, `.webp`) em `fotos/`. Subpastas viram **grupos**: as fotos de `fotos/local/` pertencem ao grupo `local`.

O **nome** de uma foto é o nome do arquivo sem a extensão: `fotos/local/sala.jpg` → `sala`. Os nomes precisam ser únicos, mesmo entre subpastas diferentes.

Fotos grandes são inseridas como cópias reduzidas (no máximo 450 px). Os originais nunca são alterados.

### No texto (`.md`)

| Você escreve | Resultado |
|---|---|
| `image(sala)` | a foto `sala` com a legenda |
| `image_group(local, 2)` | todas as fotos do grupo `local`, 2 por linha (qualquer número de colunas funciona) |
| `image_group(local, cols)` | número de colunas vindo de uma variável |

Escreva esses comandos **sozinhos na linha**. Caso contrário, a geração para e mostra a linha a corrigir.

### No modelo

A variável `pics` dá acesso a todas as fotos:

| Expressão | Resultado |
|---|---|
| `pics.all()` | lista com todas as fotos |
| `pics.group("local")` | fotos de um grupo (lista vazia se não houver) |
| `pics.get("sala")` | uma foto, ou nada se ela não existir |
| `pics.require("sala")` / `pics.require_group("local")` | o mesmo, mas para com um erro claro se faltar |
| `{% if pics %}` | verdadeiro quando há pelo menos uma foto |

Cada foto tem: `refname` (nome), `caption` (legenda), `group` (grupo), `label` (`"Foto"`), `path` (arquivo original), `reduced` (cópia usada no documento) e `thumb` (miniatura).

Para inserir uma grade de fotos diretamente no modelo:

```
{{p subdoc("image_group", pics=pics.group("anexo"), cols=2) }}
```

O `image_group` também aceita `image_width=<mm>` para forçar a largura de todas as fotos.

Para esconder uma foto de uma lista, comece o nome dela com `_` e use a função `filter_dashes`: `filter_dashes(pics.all(), "refname")`.

## Numeração automática

Toda foto inserida com `image`, `image_group` ou `caption(...)` recebe um número, na ordem em que aparece no documento: `Foto 1`, `Foto 2`…

Para citar uma foto no texto, escreva o nome dela entre `${ }`:

```
Conforme Foto ${sala}, a porta estava aberta.
```

→ "Conforme Foto 3, a porta estava aberta."

Dá para numerar outras coisas do mesmo jeito. Escreva `${Rótulo|nome}` onde o item aparece e `${nome}` onde você o cita:

```
${Tabela|valores} Valores encontrados
…
ver tabela ${valores}
```

→ "Tabela 1 Valores encontrados … ver tabela 1". Cada rótulo (`Foto`, `Tabela`, `Figura`…) tem a sua própria sequência.

A geração para com um erro quando:

- um `${nome}` cita algo que nunca foi inserido, ou
- o mesmo `${Rótulo|nome}` aparece duas vezes.

O `laudo gen --pos-edit` pula essa etapa e deixa as marcações `${...}` no documento.

## Modelos

O modelo é um documento normal do Word com marcações (sintaxe do [docxtpl](https://docxtpl.readthedocs.io/) / Jinja2):

| Sintaxe | Uso |
|---|---|
| `{{ variavel }}` | insere um valor |
| `{{ variavel\|filtro }}` | insere um valor transformado por um [filtro](#filtros) |
| `{{p laudo\|markdown }}` | insere um texto `.md` como parágrafos formatados (precisa estar sozinho no parágrafo) |
| `{%p if condicao %}` … `{%p endif %}` | mostra parágrafos só quando a condição é verdadeira |
| `{%p for item in lista %}` … `{%p endfor %}` | repete parágrafos para cada item |
| `{%tr for … %}` / `{%tc for … %}` | repete linhas / colunas de tabela |
| `{{p subdoc("nome", var=valor) }}` | insere outro `.docx` (veja abaixo) |
| `{{ image(caminho, width=50) }}` | insere uma imagem |

### Qual modelo é usado

1. O `template.docx` da pasta do projeto; senão,
2. o modelo indicado em `.laudo/.template`, procurado em `$LAUDOS_TEMPLATES_FOLDER/<nome>/template.docx`.

O `laudo gen --template <arquivo>` usa um arquivo específico.

### Modelos compartilhados

Mantenha uma pasta com uma subpasta por modelo e aponte a variável de ambiente `LAUDOS_TEMPLATES_FOLDER` para ela:

```
modelos/
└── local-de-crime/
    ├── template.docx
    ├── context.txt      # copiado para os projetos novos
    └── laudo.md         # copiado para os projetos novos
```

Numa pasta de projeto nova e vazia, `laudo init local-de-crime` seleciona o modelo e copia os outros arquivos dele (tudo, exceto `.docx`) para o projeto. O `laudo template <nome>` só seleciona o modelo, sem copiar nada.

### Subdocumentos (`subdoc`)

`{{p subdoc("capa") }}` insere o `capa.docx`. Ele é procurado na pasta do projeto, depois na pasta de modelos compartilhados e, por fim, entre os modelos que já vêm com o laudo (`image_group`).

Para passar valores ao subdocumento: `{{p subdoc("capa", titulo=nome_exame) }}`. Dentro do `capa.docx`, use `{{ titulo }}`.

### Imagens no modelo

`{{ image(caminho, width=50) }}` insere uma imagem. Os tamanhos são em **milímetros**.

- Informe `width` (largura) **ou** `height` (altura), não os dois.
- `max_height` / `max_width` limitam o outro lado: `image(p.reduced, 150, max_height=220)`.
- O arquivo precisa existir. Se não existir, aparece o texto `None` no lugar.

## Filtros

Use-os no modelo como `{{ valor|filtro }}`, ou com argumentos como `{{ valor|filtro(arg) }}`. Todos os [filtros nativos do Jinja](https://jinja.palletsprojects.com/en/stable/templates/#list-of-builtin-filters) (`upper`, `lower`, `title`, `default`, `int`, `join`, `length`, `replace`…) também funcionam.

### Texto

| Filtro | Exemplo | Resultado |
|---|---|---|
| `markdown` | `{{p laudo\|markdown }}` | texto `.md` como parágrafos formatados |
| `not_null` | `{{ x\|not_null }}` | `""` quando o valor é vazio (None) |
| `xxx` | `{{ x\|xxx }}` | `XXX` quando o valor é vazio (None) |
| `str` | `{{ 12\|str }}` | converte para texto |
| `file_stem` | `{{ "fotos/a.jpg"\|file_stem }}` | `a` |
| `join_enumerate` | `{{ ["a","b","c"]\|join_enumerate }}` | `a, b e c` |
| | `{{ ["a","b"]\|join_enumerate(true) }}` | `"a" e "b"` |
| `br` | `{{ item\|br(loop) }}` dentro de um `for` | quebra de linha antes de cada item, exceto o primeiro |
| `is_male` | `{{ "João Silva"\|is_male }}` | `True` quando o primeiro nome termina em "o" |

### Datas

| Filtro | Exemplo | Resultado |
|---|---|---|
| `data_simples` | `{{ "2026-10-15"\|data_simples }}` | `15/10/2026` |
| `data_mes_extenso` | `{{ "15/10/2026"\|data_mes_extenso }}` | `15 de outubro de 2026` (dia 1 → `1°`) |
| `datetime` | `{{ "15/10/2026"\|datetime }}` | converte texto `dd/mm/aaaa` em data |
| `data_completa` | `{{ "15/10/2026"\|datetime\|data_completa }}` | `15 (quinze) dias do mês de outubro do ano de 2026 (dois mil e vinte e seis)` |
| `dia` | `{{ d\|dia }}` | `15` |
| `dia_extenso` | `{{ d\|dia_extenso }}` | `15 (quinze)` |
| `mes_extenso` | `{{ d\|mes_extenso }}` | `outubro` |
| `hora_minuto` | `{{ d\|hora_minuto }}` | `14:05` |
| `ornow` | `{{ data_laudo\|ornow\|data_mes_extenso }}` | o valor, ou **hoje** quando estiver vazio |

`data_simples` e `data_mes_extenso` aceitam texto (`15/10/2026` ou `2026-10-15`). Já `data_completa`, `dia`, `dia_extenso`, `mes_extenso` e `hora_minuto` precisam de uma data: converta o texto antes com `|datetime`. Caso contrário, devolvem um texto vazio ou `XXX`.

### Números e valores

| Filtro | Exemplo | Resultado |
|---|---|---|
| `numero_extenso_masc` | `{{ 1234\|numero_extenso_masc }}` | `um mil, duzentos e trinta e quatro` |
| `numero_extenso_fem` | `{{ 2\|numero_extenso_fem }}` | `duas` |
| `get_extenso` | `{{ 200\|get_extenso(true) }}` | `duzentas` (`true` = feminino) |
| `moeda_extenso` | `{{ 10.5\|moeda_extenso }}` | `R$ 10,50 (dez reais e cinquenta centavos)` |

O `moeda_extenso` precisa de um número: use `{{ valor|float|moeda_extenso }}` para valores do `context.txt`.

### Números de perícia (`rg/ano`)

| Filtro | Exemplo | Resultado |
|---|---|---|
| `perrg` | `{{ "1234/2026"\|perrg }}` | `1234` |
| `perano` | `{{ "1234/2026"\|perano }}` | `2026` |
| `rgano` | `{{ "1234/2026"\|rgano }}` | `{'rg': 1234, 'ano': 2026}` |

## Funções

Chame-as no modelo como `{{ funcao(argumentos) }}`.

### Listas

| Função | Exemplo | Resultado |
|---|---|---|
| `str_list` | `str_list(relatores, revisores)` | separa textos divididos por `, ` numa única lista, ignorando valores vazios: `"a, b"`, `"c"` → `['a', 'b', 'c']` |
| `to_table` | `to_table(pics.all(), 3)` | divide uma lista em linhas de 3 (para grades) |
| `len` | `len(peritos)` | quantidade de itens |
| `join_lists` | `join_lists(a, b)` | junta listas |
| `remove_nulls` | `remove_nulls(itens, "campo")` | remove itens vazios e itens com `campo` vazio |
| `filter_dashes` | `filter_dashes(pics.all(), "refname")` | remove itens cujo campo começa com `_` |
| `count_qtd` | `count_qtd(itens, "qtd")` | soma do campo `qtd` (ou dos números da lista) |
| `get_paragraphs` | `get_paragraphs(texto)` | divide um texto em linhas |

### Gênero e plural

| Função | Exemplo | Resultado |
|---|---|---|
| `plural` | `plural("perito", 2)` | `peritos` (acrescenta `s` quando o número é > 1) |
| `ifplural` | `ifplural(peritos, "s")` | `s` quando a lista tem mais de um item; o 3º argumento é a forma singular (padrão: vazio) |
| `gender` | `gender(pessoa, "perito")` | `perita` quando `pessoa.gender` é `"F"` |
| `male_female` | `male_female(pessoa, "o", "a")` | `"o"` ou `"a"` conforme `pessoa.gender` (`"M"`/`"F"`) |

### Outras

| Função | Exemplo | Resultado |
|---|---|---|
| `not_null_or` | `not_null_or(x, "não informado")` | `x`, ou o valor padrão quando `x` está vazio |
| `case_` | `case_(tipo, {"a": "Arma", "default": "Outro"})` | o valor da chave, ou o `default` |
| `caption` | `caption("Foto", p.refname, p.caption)` | `${Foto\|sala} - legenda` (numerado depois) |
| `join_path` | `join_path("fotos", "a.jpg")` | junta partes de um caminho |
| `subdoc`, `image` | veja [Modelos](#modelos) | |

## Linha de comando

Todos os comandos aceitam `--dir <pasta>` para trabalhar em outra pasta (padrão: a pasta atual).

| Comando | O que faz |
|---|---|
| `laudo` / `laudo gui` | abre a janela principal |
| `laudo gen` | cria o `laudo.docx` |
| `laudo gen --pdf` | cria o `laudo.pdf` |
| `laudo gen --output <arquivo>` | escolhe o arquivo de saída |
| `laudo gen --template <arquivo>` | usa outro modelo |
| `laudo gen --debug [arquivo]` | mostra tudo o que é passado ao modelo (ou salva num arquivo) |
| `laudo gen --pos-edit` | mantém as marcações `${...}` sem numerá-las |
| `laudo captions` | abre o editor de legendas |
| `laudo vars` | mostra as variáveis do `context.txt` |
| `laudo context [arquivo]` | mostra (ou salva) tudo o que está disponível para o modelo, em JSON |
| `laudo init <nome>` | inicia um projeto a partir de um modelo compartilhado |
| `laudo template <nome>` | seleciona um modelo compartilhado para a pasta |
| `laudo reduce-images <origem> <destino> [--max N]` | reduz imagens: pasta → pasta, ou dentro de um `.docx`/`.odt`. Sem `--max`, pergunta o tamanho (padrão 450 px). Se o destino for igual à origem, os originais são sobrescritos |

## Solução de problemas

| Mensagem | O que fazer |
|---|---|
| `Imagem 'x' … não encontrada na pasta fotos/` | confira o nome em `image(x)` com os nomes dos arquivos (a mensagem lista os disponíveis) |
| `Grupo de imagens 'x' … não encontrado` | crie `fotos/x/` com fotos, ou corrija o nome do grupo |
| `Uso inválido de image/image_group na linha …` | deixe o comando sozinho na linha, com o número de colunas no `image_group` |
| `Referência "x" não encontrada` | o `${x}` cita uma foto ou item que não foi inserido no documento |
| `Referência "…" … está duplicada` | o mesmo item (`${Rótulo\|nome}`) foi inserido duas vezes |
| `Template 'x.docx' não encontrado` | a mensagem lista todas as pastas procuradas; adicione o arquivo ou corrija o `.laudo/.template` |
| `No filter named '…'` | esse filtro não existe, ou um filtro do laudo foi usado dentro de um `.md` (só é permitido no modelo) |
| Uma variável aparece vazia | abra **Contexto** e confira o nome exato da variável |
