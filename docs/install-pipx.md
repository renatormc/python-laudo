# Installing pipx

[pipx](https://pipx.pypa.io/) installs command-line programs such as `laudo` in their own isolated environment and puts the command on your `PATH`.

You need **Python 3.13+** installed first.

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

## After installing

**Close and reopen the terminal** so the `PATH` change takes effect. Then install laudo:

```bash
pipx install laudo
```

If Python 3.13+ is not your default Python, tell pipx which one to use:

```bash
pipx install --python python3.13 laudo
```

For other systems, see the [official pipx installation guide](https://pipx.pypa.io/stable/installation/).
