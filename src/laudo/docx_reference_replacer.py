from dataclasses import dataclass
from pathlib import Path
from docx import Document
from docx.document import Document as DocumentObject
import re
from bs4 import BeautifulSoup
from python_docx_replace import docx_replace


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


class DocxReferenceReplacer:
    def trim_var(self, val: str) -> str:
        return val.replace("\n", "")

    def check_duplicates(self, keys: Keys) -> list[ObjectNamed]:
        ret: list[ObjectNamed] = []
        found: list[str] = []
        for objects in keys.objects.values():
            for obj in objects:
                str_repr = str(obj)
                if str_repr in found:
                    ret.append(obj)
                else:
                    found.append(str_repr)
        return ret

    def extract_text_from_xml(self, xml: str) -> str:
        soup = BeautifulSoup(xml, 'xml')
        return soup.get_text()

    def get_keys_from_xml(self, xml: str) -> list[str]:
        text = self.extract_text_from_xml(xml)
        reg = re.compile(r'\$\{(.+?)\}', re.DOTALL | re.MULTILINE)
        keys = [self.trim_var(item) for item in reg.findall(text) if "#" not in item]
        return keys

    def get_all_keys(self, xml: str) -> Keys:
        keys = self.get_keys_from_xml(xml)
        ret = Keys(objects={}, references=[], all_keys=keys)
        for key in keys:
            if "|" in key:
                label, name = key.split("|")
                label, name = label.strip(), name.strip()
                try:
                    ret.objects[label].append(ObjectNamed(var_complete=key, refname=name, label=label))
                except KeyError:
                    ret.objects[label] = [ObjectNamed(var_complete=key, refname=name, label=label)]
            else:
                key = key.strip()
                if not key in ret.references:
                    ret.references.append(key)
        return ret

    def get_replacements(self, text: str) -> dict[str, str]:
        keys = self.get_all_keys(text)

        replaces: dict[str, str] = {}
        for label, objs in keys.objects.items():
            for i, obj in enumerate(objs):
                number = i + 1
                replaces[obj.refname] = str(number)
                replaces[obj.var_complete] = f"{label} {number}"
        not_found: list[str] = []
        for key in keys.all_keys:
            try:
                replaces[key]
            except KeyError:
                not_found.append(key)
        duplicates = self.check_duplicates(keys)
        lines: list[str] = []
        if duplicates:
            lines = [f"A referência \"{obj.label}- {obj.refname}\" está duplicada" for obj in duplicates]
        if not_found:
            lines += [f"Referência \"{var}\" não encontrada." for var in not_found]
        if lines:
            raise Exception("\n".join(lines))
        return replaces

    def replace_in_doc(self, doc: DocumentObject) -> None:
        replaces = self.get_replacements(doc._element.xml)
        docx_replace(doc, **replaces)

    def replace_references(self, path: Path, dest: Path | None = None) -> None:
        if not dest:
            dest = path
        doc = Document(str(path))
        self.replace_in_doc(doc)
        doc.save(str(dest))
