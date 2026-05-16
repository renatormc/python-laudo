from typing import TYPE_CHECKING

from .filters import Filters
from laudo.filters.markdown_filter import MarkdownFilter
if TYPE_CHECKING:
    from laudo.core import RenderEnv


def register(rend: 'RenderEnv') -> None:
    rend.jinja_env.filters["markdown"] = MarkdownFilter(rend)
    fs = Filters()
    for name in dir(fs):
        if not name.startswith("_"):
            method = getattr(fs, name)
            if callable(method):
                rend.jinja_env.filters[name] = method
    
