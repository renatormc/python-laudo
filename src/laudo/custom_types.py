from dataclasses import dataclass
from pathlib import Path
from docxtpl import DocxTemplate
from jinja2 import Environment


@dataclass
class RenderEnv:
    tpl: DocxTemplate
    jinja_env: Environment
    temp_folder: Path