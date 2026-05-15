from pathlib import Path
import platform
import shutil
import subprocess


def _find_libreoffice() -> str:
    for name in ("libreoffice", "soffice"):
        path = shutil.which(name)
        if path:
            return path

    if platform.system() == "Windows":
        candidates = [
            Path(r"C:\Program Files\LibreOffice\program\soffice.exe"),
            Path(r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"),
        ]
        for candidate in candidates:
            if candidate.exists():
                return str(candidate)

    raise FileNotFoundError(
        "LibreOffice not found. Install LibreOffice or add it to PATH."
    )


def convert_to_pdf(docx_path: Path, pdf_path: Path) -> Path:
    lo = _find_libreoffice()
    subprocess.run(
        [
            lo,
            "--headless",
            "--convert-to",
            "pdf",
            str(docx_path.resolve()),
            "--outdir",
            str(pdf_path.parent.resolve()),
        ],
        check=True,
        capture_output=True,
    )
    return pdf_path
