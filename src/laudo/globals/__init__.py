from jinja2 import Environment

from .._registry import public_methods
from .global_functions import GlobalFunctions


def register(jinja_env: Environment) -> None:
    jinja_env.globals.update(public_methods(GlobalFunctions()))
