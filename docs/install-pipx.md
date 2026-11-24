# Instalando o pipx

O [pipx](https://pipx.pypa.io/) instala programas de linha de comando, como o `laudo`, cada um num ambiente isolado, e coloca o comando no seu `PATH`.

Antes, você precisa ter o **Python 3.13+** instalado.

## Windows (PowerShell)

```powershell
py -m pip install --user pipx
py -m pipx ensurepath
```

## Ubuntu / Debian

```bash
sudo apt update
sudo apt install pipx
pipx ensurepath
```

## Arch Linux

```bash
sudo pacman -S python-pipx
pipx ensurepath
```

## macOS (Homebrew)

```bash
brew install pipx
pipx ensurepath
```

## Depois de instalar

**Feche e abra o terminal de novo** para a mudança no `PATH` valer. Depois, instale o laudo:

```bash
pipx install laudo
```

Se o Python 3.13+ não for o seu Python padrão, diga ao pipx qual usar:

```bash
pipx install --python python3.13 laudo
```

Para outros sistemas, veja o [guia oficial de instalação do pipx](https://pipx.pypa.io/stable/how-to/install-pipx.html).
