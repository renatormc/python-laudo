from pathlib import Path
from typing import TYPE_CHECKING
from uuid import uuid4
from docxtpl import DocxTemplate
from jinja2 import Environment

from laudo.custom_types import RenderEnv
from ..filters import register as register_filters
from ..globals import register as register_globals
from laudo.globals.inline_image import InlineImage
if TYPE_CHECKING:
    from docxtpl import Subdoc


class SubdocFunc:
    def __init__(self, renv: RenderEnv):
        self.jenv = renv

    def __call__(self, relpath: str, **kwargs) -> Subdoc:
        if not relpath.endswith(".docx"):
            relpath = f"{relpath}.docx"
        template = Path(self.jenv.tpl.template_file).parent / relpath
        if not template.is_file():
            raise FileNotFoundError(f"Subdocument template not found: {template}")
        if not kwargs:
            return self.jenv.tpl.new_subdoc(str(template))

        renv = RenderEnv(
            tpl=DocxTemplate(str(template)),
            jinja_env=Environment(),
            temp_folder=self.jenv.temp_folder,
        )
        register_filters(renv.jinja_env)

        renv.jinja_env.globals["subdoc"] = SubdocFunc(renv)
        renv.jinja_env.globals["image"] = InlineImage(renv)
        register_globals(renv.jinja_env)
        renv.tpl.render(kwargs, jinja_env=renv.jinja_env)
        output_path = self.jenv.temp_folder / f"{uuid4().hex}.docx"
        renv.tpl.save(str(output_path))
        return self.jenv.tpl.new_subdoc(str(output_path))
