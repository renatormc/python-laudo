import os
from pathlib import Path
import shutil
import re
from tempfile import mkdtemp
import zipfile
import xml.dom.minidom
from xml.dom.minidom import parseString, Document


class DocZip:
    def __init__(self, path: Path | str, local=False) -> None:
        self.path = Path(path)
        self.local = local
        self.parsed: dict[str, Document] = {}

    def __enter__(self):
        self.dest_dir = self.path.parent / self.path.stem if self.local else Path(mkdtemp())
        with zipfile.ZipFile(self.path, 'r') as zip_ref:
            zip_ref.extractall(self.dest_dir)
        return self

    def __exit__(self, type, value, tb):
        if not self.local:
            shutil.rmtree(self.dest_dir)

    def _parse_file(self,  relpath: str) -> Document:
        path = self.dest_dir / relpath
        if not path.is_file():
            raise Exception(f"File {relpath} not found in doczip")
        text = path.read_text(encoding="utf-8")
        return parseString(text)

    def xml(self, relpath: str) -> Document:
        if relpath not in self.parsed:
            self.parsed[relpath] = self._parse_file(relpath)
        return self.parsed[relpath]

    def save(self, path: str | Path | None = None) -> None:
        if path is None:
            path = self.path
        for relpath, doc in self.parsed.items():
            doc_path = self.dest_dir / relpath
            doc_path.write_text(doc.toxml(), encoding="utf-8")
        with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as new_zip:
            for root_dir, _, files in os.walk(self.dest_dir):
                for file in files:
                    file_path = os.path.join(root_dir, file)
                    arcname = os.path.relpath(file_path, self.dest_dir)
                    new_zip.write(file_path, arcname)


def get_docmaker_id(doc: DocZip) -> str:
    meta = doc.xml("meta.xml")
    for el in meta.getElementsByTagName('meta:user-defined'):
        if el.getAttribute('meta:name') == "DocmakerID":
            child = el.firstChild
            if child is None:
                continue
            val = getattr(child, "nodeValue", None)
            if val is None:
                val = getattr(child, "data", None)
            if val is None:
                val = getattr(el, "textContent", None)
            if val is not None:
                return val
    raise Exception("DocmakerID not found")


def set_docmaker_id(doc: DocZip, id: str) -> None:
    meta = doc.xml("meta.xml")
    for el in meta.getElementsByTagName('meta:user-defined'):
        if el.getAttribute('meta:name') == "DocmakerID":
            child = el.firstChild
            if child is None:
                child = meta.createTextNode(id)
                el.appendChild(child)
            else:
                if hasattr(child, "nodeValue"):
                    child.nodeValue = id
                elif hasattr(child, "data"):
                    child.data = id
                else:
                    # remove any existing child nodes and append a new text node
                    while el.firstChild:
                        el.removeChild(el.firstChild)
                    el.appendChild(meta.createTextNode(id))
            return
    new_el = meta.createElement('meta:user-defined')
    new_el.setAttribute('meta:name', "DocmakerID")
    text_node = meta.createTextNode(id)
    new_el.appendChild(text_node)
    # documentElement can be None according to type hints; append to document if so
    if meta.documentElement is None:
        meta.appendChild(new_el)
    else:
        meta.documentElement.appendChild(new_el)


class DocxZip:
    def __init__(self, path: Path | str, local=False) -> None:
        self.path = Path(path)
        self.local = local
        self._document_xml: str | None = None
       

    def __enter__(self):
        self.dest_dir = self.path.parent / f"{self.path.name}_" if self.local else Path(mkdtemp())
        self.path_document_xml = self.dest_dir / "word/document.xml" if self.path.suffix.lower() == ".docx" else self.dest_dir / "content.xml"
        self.image_folder = self.dest_dir / "word/media" if self.path.suffix.lower() == ".docx" else self.dest_dir / "Pictures"
        with zipfile.ZipFile(self.path, 'r') as zip_ref:
            zip_ref.extractall(self.dest_dir)
        return self

    def __exit__(self, type, value, tb):
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
        self.document_xml = "\n".join([line for line in pretty_xml_as_string.split('\n') if line.strip()])

    def save_xml(self) -> None:
        self.path_document_xml.write_text(self.document_xml, encoding="utf-8")

    def save(self, path: str | Path | None = None) -> None:
        if path is None:
            path = self.path
        if self._document_xml is not None:
            self.path_document_xml.write_text(self._document_xml, encoding="utf-8")
        with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as new_zip:
            for root_dir, _, files in os.walk(self.dest_dir):
                for file in files:
                    file_path = os.path.join(root_dir, file)
                    arcname = os.path.relpath(file_path, self.dest_dir)
                    new_zip.write(file_path, arcname)
