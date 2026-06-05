from pathlib import Path
from typing import TYPE_CHECKING
from uuid import uuid4
from docxtpl import DocxTemplate
from jinja2 import Environment

from laudo.custom_types import RenderEnv
from laudo.template import get_template
from ..filters import register as register_filters
from ..globals import register as register_globals
from laudo.globals.inline_image import InlineImage
if TYPE_CHECKING:
    from docxtpl import Subdoc


class SubdocFunc:
    def __init__(self, renv: RenderEnv, *, workdir: Path):
        self.jenv = renv
        self.workdir = workdir

    def __call__(self, relpath: str, **kwargs) -> Subdoc:
        if not relpath.endswith(".docx"):
            relpath = f"{relpath}.docx"
        try:
            template = get_template(Path(relpath).stem, self.workdir)
        except FileNotFoundError as e:
            raise FileNotFoundError(
                f"Subdocument template not found: {relpath}"
            ) from e
        if not kwargs:
            return self.jenv.tpl.new_subdoc(str(template))

        renv = RenderEnv(
            tpl=DocxTemplate(str(template)),
            jinja_env=Environment(),
            temp_folder=self.jenv.temp_folder,
        )
        register_filters(renv.jinja_env)

        renv.jinja_env.globals["subdoc"] = SubdocFunc(renv, workdir=self.workdir)
        renv.jinja_env.globals["image"] = InlineImage(renv)
        register_globals(renv.jinja_env)
        renv.tpl.render(kwargs, jinja_env=renv.jinja_env)
        output_path = self.jenv.temp_folder / f"{uuid4().hex}.docx"
        renv.tpl.save(str(output_path))
        return self.jenv.tpl.new_subdoc(str(output_path))
