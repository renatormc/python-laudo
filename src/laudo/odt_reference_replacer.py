from pathlib import Path
import re
from typing import Iterator, Pattern
from laudo.docxzip import DocZip
from xml.dom.minidom import Document, Node


class RefManager:
    def __init__(self) -> None:
        self.current: dict[str, int] = {}
        self.bookmarks: dict[str, int] = {}
        self.waiting_ref: dict[str, list[str]] = {}
        self._replaces: dict[str, str] = {}
        self.pattern = r'\$\{(.+?)\}'

    def increment_number(self, cat: str) -> int:
        cur = self.current.get(cat)
        if cur is None:
            self.current[cat] = 1
            return 1
        new = cur + 1
        self.current[cat] = new
        return new
    
        
    def add_var(self, text: str) -> None:
        val = re.match(self.pattern, text)
        if not val:
            raise Exception("Wrong value")
        var = val.group(1)
        if "|" in var:
            cat, bookmark = var.split("|")
            cat, bookmark = cat.strip(), bookmark.strip()
            number = self.increment_number(cat)
            if bookmark in self.bookmarks:
                raise Exception(f"bookmark {bookmark} duplicated")
            self.bookmarks[bookmark] = number
            self._replaces[text] = f"{cat} {number}"

            waiting = self.waiting_ref.get(bookmark)
            if waiting:
                for w in waiting:
                    self._replaces[w] = str(number)
                del self.waiting_ref[bookmark]

            return
        
        bookmark=var
        replace_number = self.bookmarks.get(bookmark)
        if replace_number:
            self._replaces[text] = str(replace_number)
        else:
            try:
                self.waiting_ref[bookmark].append(text)
            except KeyError:
                self.waiting_ref[bookmark] = [text]
    
    def get_replaces(self) -> dict[str, str]:
        if self.waiting_ref:
            items = ", ".join(self.waiting_ref.keys())
            raise Exception(f"Bookmark(s) \"{items}\" not found")
        return self._replaces

class OdtReferenceReplacer:


    def _iter_text_nodes(self, node: Node) -> Iterator[Node]:
        for child in node.childNodes:
            if child.nodeType in (Node.TEXT_NODE, Node.CDATA_SECTION_NODE):
                yield child
            else:
                yield from self._iter_text_nodes(child)


    def iter_xml_regex_matches(self, doc: Document | Node, pattern: str | Pattern[str]) -> Iterator[re.Match[str]]:
        compiled = re.compile(pattern) if isinstance(pattern, str) else pattern
        root = doc.documentElement if hasattr(doc, "documentElement") else doc
        for text_node in self._iter_text_nodes(root):
            for match in compiled.finditer(text_node.data): #type: ignore
                yield match


    def replace(self, path: str | Path, dest: str | Path) -> None:
        path = Path(path)
        dest = Path(dest)
        with DocZip(path) as doc:
            rm = RefManager()
            xml_doc = doc.xml("content.xml")
            for match in self.iter_xml_regex_matches(xml_doc, rm.pattern):
                rm.add_var(match.group(0))
            replaces = rm.get_replaces()
            for node in self._iter_text_nodes(xml_doc):
                for var, value in replaces.items():
                    node.data = node.data.replace(var, value) #type: ignore
            doc.save(dest)
