from typing import TYPE_CHECKING

from .filters import rgano
from laudo.filters.markdown_filter import MarkdownFilter
if TYPE_CHECKING:
    from laudo.core import RenderEnv


def register(rend: 'RenderEnv') -> None:
    rend.jinja_env.filters["markdown"] = MarkdownFilter(rend)
    rend.jinja_env.filters["rgano"] = rgano
