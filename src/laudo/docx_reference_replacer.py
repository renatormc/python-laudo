import re
from dataclasses import dataclass
from pathlib import Path

from docx import Document
from docx.document import Document as DocumentObject
from bs4 import BeautifulSoup
from python_docx_replace.paragraph import Paragraph

from .errors import LaudoError

_KEY_RE = re.compile(r'\$\{(.+?)\}', re.DOTALL | re.MULTILINE)


def docx_replace(doc: DocumentObject, replaces: dict[str, str]) -> None:
    """Same result as ``python_docx_replace.docx_replace(doc, **replaces)``, much faster.

    The library loops *keys x paragraphs* and recomputes each paragraph's text
    (an XPath query per run) on every iteration. Here each paragraph's text is
    read once, paragraphs without ``${`` are skipped, and only the keys present
    in a paragraph are replaced, using the library's own run-aware replacement.
    """
    wrapped = [(f"${{{key}}}", str(value)) for key, value in replaces.items()]
    for p in Paragraph.get_all(doc):
        text = p.text
        if "${" not in text:
            continue
        paragraph = Paragraph(p)
        for key, value in wrapped:
            if key in text:
                paragraph.replace_key(key, value)


@dataclass
class ObjectNamed:
    var_complete: str
    label: str
    refname: str

    def __repr__(self):
        return f"{self.label}_{self.refname}"


@dataclass
class Keys:
    objects: dict[str, list[ObjectNamed]]
    references: list[str]
    all_keys: list[str]

@dataclass
class ReferenceReplaceResult:
    replaces: dict[str, str]
    not_found: list[str]
    duplicates: list[ObjectNamed]


def raise_reference_errors(errors: list[str]) -> None:
    if errors:
        details = "\n".join(f"- {error}" for error in errors)
        raise LaudoError(f"Erros encontrados durante a substituição de referências:\n{details}")


class DocxReferenceReplacer:
    def trim_var(self, val: str) -> str:
        return val.replace("\n", "")

    def check_duplicates(self, keys: Keys) -> list[ObjectNamed]:
        ret: list[ObjectNamed] = []
        found: set[str] = set()
        for objects in keys.objects.values():
            for obj in objects:
                str_repr = str(obj)
                if str_repr in found:
                    ret.append(obj)
                else:
                    found.add(str_repr)
        return ret

    def extract_text_from_xml(self, xml: str) -> str:
        # BeautifulSoup is lenient: the rendered XML may contain undeclared
        # namespace prefixes (from docxtpl subdocs) that strict parsers reject.
        return BeautifulSoup(xml, "xml").get_text()

    def get_keys_from_xml(self, xml: str) -> list[str]:
        text = self.extract_text_from_xml(xml)
        return [self.trim_var(item) for item in _KEY_RE.findall(text) if "#" not in item]

    def get_all_keys(self, xml: str) -> Keys:
        keys = self.get_keys_from_xml(xml)
        ret = Keys(objects={}, references=[], all_keys=keys)
        seen_refs: set[str] = set()
        for key in keys:
            if "|" in key:
                label, name = key.split("|")
                label, name = label.strip(), name.strip()
                ret.objects.setdefault(label, []).append(ObjectNamed(var_complete=key, refname=name, label=label))
            else:
                key = key.strip()
                if key not in seen_refs:
                    seen_refs.add(key)
                    ret.references.append(key)
        return ret

    def get_replacements(self, text: str) -> ReferenceReplaceResult:
        keys = self.get_all_keys(text)
        replaces: dict[str, str] = {}
        for label, objs in keys.objects.items():
            for i, obj in enumerate(objs):
                number = i + 1
                replaces[obj.refname] = str(number)
                replaces[obj.var_complete] = f"{label} {number}"
        not_found = [key for key in keys.all_keys if key not in replaces]
        duplicates = self.check_duplicates(keys)
        return ReferenceReplaceResult(replaces=replaces, not_found=not_found, duplicates=duplicates)

    def replace_in_doc(self, doc: DocumentObject) -> list[str]:
        replaces = self.get_replacements(doc._element.xml)
        lines = [f"Referência \"{var}\" não encontrada." for var in replaces.not_found] + [ f"Referência \"{obj.var_complete}\" do tipo \"{obj.label}\" está duplicada." for obj in replaces.duplicates]
        docx_replace(doc, replaces.replaces)
        return lines

    def replace_references(self, path: Path, dest: Path | None = None) -> None:
        if not dest:
            dest = path
        doc = Document(str(path))
        raise_reference_errors(self.replace_in_doc(doc))
        doc.save(str(dest))
