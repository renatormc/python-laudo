from jinja2 import Environment

from .._registry import public_methods
from .filters import Filters


def register(jinja_env: Environment) -> None:
    jinja_env.filters.update(public_methods(Filters()))
