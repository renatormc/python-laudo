import docxtpl
from pathlib import Path
from PIL import Image as PilImage
from docx.shared import Mm
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from laudo.core import RenderEnv

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
        path = Path(file)
        if not path.exists():
            return None
        img = PilImage.open(path)
        alfa = img.height/img.width
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