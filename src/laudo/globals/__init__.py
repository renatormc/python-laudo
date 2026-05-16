from typing import TYPE_CHECKING
from laudo.globals.subdoc_func import SubdocFunc
from .global_functions import GlobalFunctions
from .inline_image import InlineImage
if TYPE_CHECKING:
    from laudo.core import RenderEnv

def register(renv: 'RenderEnv') -> None:
    renv.jinja_env.globals["subdoc"] = SubdocFunc(renv)
    renv.jinja_env.globals["image"] = InlineImage(renv)
    gf = GlobalFunctions()
    for name in dir(gf):
        if not name.startswith("_"):
            method = getattr(gf, name)
            if callable(method):
                renv.jinja_env.globals[name] = method   

