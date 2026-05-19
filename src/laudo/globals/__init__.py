from .global_functions import GlobalFunctions
from jinja2 import Environment


def register(jinja_env: 'Environment') -> None:
    gf = GlobalFunctions()
    for name in dir(gf):
        if not name.startswith("_"):
            method = getattr(gf, name)
            if callable(method):
                jinja_env.globals[name] = method   

