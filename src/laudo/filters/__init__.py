from .filters import Filters
from laudo.filters.markdown_filter import MarkdownFilter
from jinja2 import Environment



def register(jinja_env: 'Environment') -> None:
    fs = Filters()
    for name in dir(fs):
        if not name.startswith("_"):
            method = getattr(fs, name)
            if callable(method):
                jinja_env.filters[name] = method
    
