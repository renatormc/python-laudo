import re
import shutil
import xml.dom.minidom
import zipfile
from pathlib import Path
from tempfile import mkdtemp


def _zip_dir(src_dir: Path, dest: str | Path) -> None:
    """Zip ``src_dir`` into ``dest`` as an Office/ODF package.

    ODF requires ``mimetype`` to be the first entry and stored uncompressed,
    otherwise LibreOffice may reject the file.
    """
    files = sorted(p for p in src_dir.rglob("*") if p.is_file())
    mimetype = src_dir / "mimetype"
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as new_zip:
        if mimetype.is_file():
            new_zip.write(mimetype, "mimetype", compress_type=zipfile.ZIP_STORED)
        for file in files:
            if file != mimetype:
                new_zip.write(file, file.relative_to(src_dir).as_posix())


class DocxZip:
    def __init__(self, path: Path | str, local: bool = False) -> None:
        self.path = Path(path)
        self.local = local
        self._document_xml: str | None = None

    def __enter__(self) -> "DocxZip":
        self.dest_dir = self.path.parent / f"{self.path.name}_" if self.local else Path(mkdtemp())
        is_docx = self.path.suffix.lower() == ".docx"
        self.path_document_xml = self.dest_dir / ("word/document.xml" if is_docx else "content.xml")
        self.image_folder = self.dest_dir / ("word/media" if is_docx else "Pictures")
        with zipfile.ZipFile(self.path, "r") as zip_ref:
            zip_ref.extractall(self.dest_dir)
        return self

    def __exit__(self, type, value, tb) -> None:
        if not self.local:
            shutil.rmtree(self.dest_dir)

    @property
    def document_xml(self) -> str:
        if self._document_xml is None:
            self._document_xml = self.path_document_xml.read_text(encoding="utf-8")
        return self._document_xml

    @document_xml.setter
    def document_xml(self, value: str) -> None:
        self._document_xml = value

    def replace_regex(self, pattern: str, replace: str) -> None:
        reg = re.compile(pattern, re.MULTILINE | re.DOTALL)
        self.document_xml = reg.sub(replace, self.document_xml)

    def replace(self, old: str, new: str) -> None:
        self.document_xml = self.document_xml.replace(old, new)

    def pretty_format_xml(self) -> None:
        dom = xml.dom.minidom.parseString(self.document_xml)
        pretty_xml_as_string = dom.toprettyxml(indent="  ")
        self.document_xml = "\n".join(line for line in pretty_xml_as_string.split("\n") if line.strip())

    def save_xml(self) -> None:
        self.path_document_xml.write_text(self.document_xml, encoding="utf-8")

    def save(self, path: str | Path | None = None) -> None:
        if self._document_xml is not None:
            self.save_xml()
        _zip_dir(self.dest_dir, path if path is not None else self.path)
