import json
from pathlib import Path

from d_pygen.logger import logger
from d_pygen.config import CONFIG_DIR


TEMPLATES_DIR = CONFIG_DIR / "templates"


class TemplateNotFound(Exception):
    pass


class TemplateVariantNotFound(Exception):
    pass


def get_template_path(template_name: str, variant: str = "default") -> Path:

    template_root = TEMPLATES_DIR / template_name

    if not template_root.exists():
        raise TemplateNotFound(
            f"Template '{template_name}' not found"
        )

    variant_path = template_root / variant

    if not variant_path.exists():
        raise TemplateVariantNotFound(
            f"Variant '{variant}' not found in template '{template_name}'"
        )

    return variant_path


def load_template(template_name: str, variant: str = "default") -> dict:
    """
    Load template and return plan dict compatible with create_project()
    """

    logger.info(f"Loading template: {template_name} ({variant})")

    template_path = get_template_path(template_name, variant)

    template_json = template_path / "template.json"

    files_dir = template_path / "files"

    if not template_json.exists():
        raise Exception("template.json missing")

    if not files_dir.exists():
        raise Exception("files directory missing")

    template_config = json.loads(
        template_json.read_text(encoding="utf-8")
    )

    project_name = template_config.get("project_name", template_name)

    folders = []
    files = {}

    # Walk files directory
    for path in files_dir.rglob("*"):

        relative = path.relative_to(files_dir)

        if path.is_dir():

            folders.append(str(relative))

        else:

            files[str(relative)] = path.read_text(
                encoding="utf-8"
            )

    plan = {
        "project_name": project_name,
        "folders": folders,
        "files": files
    }

    logger.info("Template loaded successfully")

    return plan


def list_templates():

    if not TEMPLATES_DIR.exists():
        return []

    return [
        p.name
        for p in TEMPLATES_DIR.iterdir()
        if p.is_dir()
    ]


def list_variants(template_name: str):

    template_root = TEMPLATES_DIR / template_name

    if not template_root.exists():
        return []

    return [
        p.name
        for p in template_root.iterdir()
        if p.is_dir()
    ]
