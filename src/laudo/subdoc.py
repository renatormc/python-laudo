from pathlib import Path

from docxtpl import DocxTemplate
from docxtpl.subdoc import Subdoc
from lxml import etree  # type: ignore[import-untyped]


class NamespaceSafeSubdoc(Subdoc):
    """``Subdoc`` that keeps namespace declarations in the inserted XML.

    docxtpl serializes the subdocument ``<w:body>`` and strips the ``<w:body>``
    tags with a regex. lxml puts the namespace declarations inherited from the
    root (e.g. ``xmlns:a`` used by images) on that very tag, so they are lost,
    and the master document ends up with undeclared prefixes such as
    ``a:graphicFrameLocks`` (invalid XML: Word may refuse to open it).

    Serializing each body child on its own makes lxml declare the namespaces
    on every inserted element, so the fragment is valid wherever it lands.
    """

    def _get_xml(self) -> str:
        body = self.subdocx.element.body
        if body.sectPr is not None:
            body.remove(body.sectPr)
        return "".join(etree.tostring(child, encoding="unicode") for child in body)


def new_subdoc(tpl: DocxTemplate, docpath: Path | str | None = None) -> Subdoc:
    """Drop-in replacement for ``tpl.new_subdoc(docpath)``."""
    tpl.init_docx()
    return NamespaceSafeSubdoc(tpl, str(docpath) if docpath is not None else None)
