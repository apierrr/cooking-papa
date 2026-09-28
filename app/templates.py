import time
from fastapi.templating import Jinja2Templates
from pathlib import Path

from .schemas import CATEGORIES

TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
templates.env.globals["asset_version"] = str(int(time.time()))
templates.env.globals["CATEGORIES"] = CATEGORIES
