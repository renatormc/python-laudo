import subprocess
import sys
from pathlib import Path


def test_cli_help():
    result = subprocess.run(
        [sys.executable, "-m", "laudo", "--help"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "Usage:" in result.stdout
    assert "--install" in result.stdout
    assert "--dir" in result.stdout
    assert "--gui" in result.stdout
    assert "--debug" in result.stdout


def test_cli_converts_docx(sample_project: Path):
    result = subprocess.run(
        [sys.executable, "-m", "laudo"],
        capture_output=True, text=True,
        cwd=str(sample_project),
    )
    assert result.returncode == 0
    assert "Generated:" in result.stdout
    output = sample_project / "laudo.docx"
    assert output.is_file()
    assert output.stat().st_size > 0


def test_cli_debug_shows_context(sample_project: Path):
    result = subprocess.run(
        [sys.executable, "-m", "laudo", "--debug"],
        capture_output=True, text=True,
        cwd=str(sample_project),
    )
    assert result.returncode == 0
    assert "--- context ---" in result.stdout
    assert "intro" in result.stdout
    assert "chapter_1" in result.stdout


def test_cli_converts_with_dir_flag(sample_project: Path):
    result = subprocess.run(
        [sys.executable, "-m", "laudo", "--dir", str(sample_project)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "Generated:" in result.stdout
    output = sample_project / "laudo.docx"
    assert output.is_file()
    assert output.stat().st_size > 0


def test_cli_install():
    result = subprocess.run(
        [sys.executable, "-m", "laudo", "--install"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "Installed" in result.stdout
