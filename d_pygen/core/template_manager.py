from pathlib import Path

from d_pygen.config import CONFIG_DIR

TEMPLATE_DIR = CONFIG_DIR / "templates"


def list_templates():

    if not TEMPLATE_DIR.exists():
        return []

    return [

        d.name

        for d in TEMPLATE_DIR.iterdir()

        if d.is_dir()

    ]
