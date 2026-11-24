from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from uuid import uuid4

from docxtpl import DocxTemplate

from laudo.custom_types import RenderEnv
from laudo.errors import TemplateNotFoundError
from laudo.subdoc import new_subdoc
from laudo.template import get_template

if TYPE_CHECKING:
    from docxtpl import Subdoc


class SubdocFunc:
    def __init__(self, renv: RenderEnv, *, workdir: Path):
        self.jenv = renv
        self.workdir = workdir
        self._templates: dict[str, Path] = {}

    def _resolve(self, name: str) -> Path:
        # The same subdoc (e.g. image_group) is usually used many times per render.
        if name not in self._templates:
            try:
                self._templates[name] = get_template(name, self.workdir)
            except TemplateNotFoundError as e:
                raise TemplateNotFoundError(f"subdoc('{name}'): {e}") from e
        return self._templates[name]

    def __call__(self, relpath: str, **kwargs) -> Subdoc:
        template = self._resolve(Path(relpath).stem)
        if not kwargs:
            return new_subdoc(self.jenv.tpl, template)

        from laudo.render_env import create_render_env

        renv = create_render_env(DocxTemplate(str(template)), self.jenv.temp_folder, self.workdir)
        renv.tpl.render(kwargs, jinja_env=renv.jinja_env)
        output_path = self.jenv.temp_folder / f"{uuid4().hex}.docx"
        renv.tpl.save(str(output_path))
        return new_subdoc(self.jenv.tpl, output_path)
