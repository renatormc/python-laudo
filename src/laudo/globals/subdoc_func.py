from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from docxtpl import Subdoc
    from laudo.core import RenderEnv

class SubdocFunc:
    def __init__(self, renv: RenderEnv):
        self.jenv = renv

    def __call__(self, relpath: str) -> Subdoc:
        return self.jenv.tpl.new_subdoc(str(self.jenv.assets_folder / relpath))