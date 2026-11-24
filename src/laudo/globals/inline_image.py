import docxtpl
from pathlib import Path
from PIL import Image as PilImage
from docx.shared import Mm
from typing import TYPE_CHECKING
from jinja2 import Undefined
from laudo.errors import ImageNotFoundError
if TYPE_CHECKING:
    from laudo.custom_types import RenderEnv

class InlineImage:
    def __init__(self, renv: 'RenderEnv') -> None:
        self.tpl = renv.tpl

    def __call__(self, file: str | Path,
                 width: int | None = None,
                 height: int | None = None,
                 max_width: int | None = None,
                 max_height: int | None = None,
                 ) -> docxtpl.InlineImage | None:
        if width is None and height is None:
            raise Exception("width or height is required")
        if width is not None and height is not None:
            raise Exception("only width or height can be specified, not both")
        if file is None or isinstance(file, Undefined):
            hint = f" ({file._undefined_message})" if isinstance(file, Undefined) else ""
            raise ImageNotFoundError(
                f"image(): caminho da imagem indefinido{hint}. "
                "Verifique se a variável/imagem passada para image(...) existe no contexto."
            )
        path = Path(file)
        if not path.exists():
            return None
        with PilImage.open(path) as img:  # reads only the header; closes the file handle
            alfa = img.height / img.width
        parms = {}
        if width is not None:
            if max_height is not None and alfa*width > max_height:
                parms['height'] = Mm(max_height)
            else:
                parms['width'] = Mm(width)
        elif height is not None:
            if max_width is not None and height/alfa > max_width:
                parms['width'] = Mm(max_width)
            else:
                parms['height'] = Mm(height)

        return docxtpl.InlineImage(self.tpl, str(file), **parms)