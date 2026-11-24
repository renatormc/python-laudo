from pathlib import Path

from docxtpl import DocxTemplate
from jinja2 import Environment

from .custom_types import RenderEnv


def create_render_env(tpl: DocxTemplate, temp_folder: Path, workdir: Path) -> RenderEnv:
    """Build a RenderEnv with every laudo filter and global registered.

    Shared by the main render and by ``subdoc(...)`` so both see the same
    Jinja environment (filters, ``image``, ``subdoc`` and helper globals).
    """
    from .filters import register as register_filters
    from .filters.markdown_filter import MarkdownFilter
    from .globals import register as register_globals
    from .globals.inline_image import InlineImage
    from .globals.subdoc_func import SubdocFunc

    renv = RenderEnv(tpl=tpl, jinja_env=Environment(), temp_folder=temp_folder)
    env = renv.jinja_env
    register_filters(env)
    env.filters["markdown"] = MarkdownFilter(renv)
    register_globals(env)
    env.globals["subdoc"] = SubdocFunc(renv, workdir=workdir)
    env.globals["image"] = InlineImage(renv)
    return renv
