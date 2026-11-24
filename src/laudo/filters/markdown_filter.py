from __future__ import annotations

import re
from typing import TYPE_CHECKING
from uuid import uuid4

from docx import Document
from docx.shared import Pt
from docx.text.paragraph import Paragraph

from laudo.subdoc import new_subdoc

if TYPE_CHECKING:
    from docxtpl import Subdoc

    from laudo.custom_types import RenderEnv


_HEADING_RE = re.compile(r"^(#{1,3}) ")
_INLINE_SPLIT_RE = re.compile(r"(\*\*.*?\*\*|\*.*?\*)")
_BOLD_RE = re.compile(r"\*\*(.*?)\*\*")
_ITALIC_RE = re.compile(r"\*(.*?)\*")
_LIST_INDENT = Pt(18)
_BULLET_HANGING = Pt(-9)


def _compact(paragraph: Paragraph) -> Paragraph:
    """Remove the spacing before/after a paragraph."""
    paragraph.paragraph_format.space_before = Pt(0)
    paragraph.paragraph_format.space_after = Pt(0)
    return paragraph


def _add_inline_runs(paragraph: Paragraph, text: str) -> None:
    """Add ``text`` to ``paragraph`` handling **bold** and *italic* markers."""
    for token in _INLINE_SPLIT_RE.split(text):
        if m := _BOLD_RE.match(token):
            paragraph.add_run(m.group(1)).bold = True
        elif m := _ITALIC_RE.match(token):
            paragraph.add_run(m.group(1)).italic = True
        else:
            paragraph.add_run(token)


class MarkdownFilter:
    def __init__(self, renv: RenderEnv):
        self.jenv = renv

    def __call__(self, md_text: str) -> Subdoc:
        document = Document()

        for line in md_text.split("\n"):
            stripped = line.strip()
            if not stripped:
                continue  # skip blank lines instead of adding empty paragraphs

            if heading := _HEADING_RE.match(stripped):
                level = len(heading.group(1))
                _compact(document.add_heading(stripped[level + 1:], level=level))
            elif stripped.startswith("- "):
                # Keep the `Normal` style but make it look like a bulleted list
                item = _compact(document.add_paragraph(style="Normal"))
                item.add_run("• ")
                _add_inline_runs(item, stripped[2:])
                item.paragraph_format.left_indent = _LIST_INDENT
                item.paragraph_format.first_line_indent = _BULLET_HANGING
            else:
                _add_inline_runs(_compact(document.add_paragraph(style="Normal")), line)

        tempdocx = self.jenv.temp_folder / f"{uuid4().hex}.docx"
        document.save(str(tempdocx))
        return new_subdoc(self.jenv.tpl, tempdocx)
