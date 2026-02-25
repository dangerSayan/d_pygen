import json
import shutil
import tempfile
import subprocess
from pathlib import Path
from rich.console import Console

console = Console()


# ============================================================
# REQUIRED STRUCTURE RULES
# ============================================================

REQUIRED_TEMPLATE_FILES = [
    "template.json",
    "files"
]

REQUIRED_TEMPLATE_JSON_FIELDS = [
    "name",
    "description"
]


# ============================================================
# SAFE JSON LOAD
# ============================================================

def load_json_safe(path: Path):

    try:

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    except Exception as e:

        raise Exception(f"Invalid JSON: {path.name} ({str(e)})")


# ============================================================
# VALIDATE template.json
# ============================================================

def validate_template_json(template_json_path: Path):

    data = load_json_safe(template_json_path)

    missing = []

    for field in REQUIRED_TEMPLATE_JSON_FIELDS:

        if field not in data:
            missing.append(field)

    if missing:

        raise Exception(
            f"template.json missing required fields: {', '.join(missing)}"
        )

    return True


# ============================================================
# VALIDATE files folder
# ============================================================

def validate_files_folder(files_path: Path):

    if not files_path.exists():

        raise Exception("files/ folder missing")

    if not any(files_path.iterdir()):

        raise Exception("files/ folder is empty")

    return True


# ============================================================
# VALIDATE TEMPLATE VARIANT
# ============================================================

def validate_variant(variant_path: Path):

    template_json = variant_path / "template.json"
    files_dir = variant_path / "files"

    if not template_json.exists():

        raise Exception(
            f"Missing template.json in {variant_path}"
        )

    validate_template_json(template_json)

    validate_files_folder(files_dir)

    return True


# ============================================================
# VALIDATE TEMPLATE
# ============================================================

def validate_template(template_path: Path):

    if not template_path.exists():

        raise Exception(
            f"Template folder missing: {template_path}"
        )

    variants = list(template_path.iterdir())

    if not variants:

        raise Exception(
            f"No variants found in template: {template_path.name}"
        )

    for variant in variants:

        if variant.is_dir():

            validate_variant(variant)

    return True


# ============================================================
# VALIDATE FULL PLUGIN STRUCTURE
# ============================================================

def validate_plugin_structure(plugin_path: Path):

    templates_dir = plugin_path / "templates"

    if not templates_dir.exists():

        raise Exception("Missing templates/ folder")

    templates = list(templates_dir.iterdir())

    if not templates:

        raise Exception("No templates found")

    for template in templates:

        if template.is_dir():

            validate_template(template)

    return True


# ============================================================
# CLONE REPO
# ============================================================

def clone_repo(repo_url: str, branch="main"):

    if not shutil.which("git"):
        raise Exception("Git not installed or not found in PATH")

    temp_dir = Path(tempfile.mkdtemp())

    try:

        subprocess.run(
            [
                "git",
                "clone",
                "--depth",
                "1",
                "-b",
                branch,
                repo_url,
                str(temp_dir)
            ],
            check=True,
            capture_output=True
        )

        return temp_dir

    except FileNotFoundError:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise Exception("Git executable not found")

    except subprocess.CalledProcessError:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise Exception("Failed to clone repository")

    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise Exception(str(e))

# ============================================================
# VALIDATE FROM LOCAL PATH
# ============================================================

def validate_local_plugin(plugin_path: str):

    plugin_path = Path(plugin_path)

    console.print(
        f"[bold cyan]Validating plugin:[/bold cyan] {plugin_path}"
    )

    try:

        validate_plugin_structure(plugin_path)

        console.print(
            "[green]✔ Plugin structure valid[/green]"
        )

        return True

    except Exception as e:

        console.print(
            f"[red]✘ Validation failed:[/red] {str(e)}"
        )

        return False


# ============================================================
# VALIDATE FROM GITHUB
# ============================================================



def validate_github_plugin(repo_url: str, branch="main"):

    if not shutil.which("git"):
        console.print("[bold red]✘ Git not found in system.[/bold red]")
        console.print("[yellow]Install Git and restart terminal:[/yellow]")
        console.print("https://git-scm.com/downloads\n")
        return False


    console.print(
        f"[bold cyan]Validating GitHub plugin:[/bold cyan] {repo_url}"
    )

    temp_dir = None

    try:

        temp_dir = clone_repo(repo_url, branch)

        validate_plugin_structure(temp_dir)

        console.print(
            "[green]✔ Plugin validation successful[/green]"
        )

        return True

    except Exception as e:

        console.print(
            f"[bold red]✘ Plugin validation failed[/bold red]\n"
            f"[yellow]Reason:[/yellow] {str(e)}"
        )

        return False

    finally:

        if temp_dir and temp_dir.exists():

            try:

                shutil.rmtree(temp_dir)

            except PermissionError:

                # Windows fix: force remove read-only files
                def onerror(func, path, exc_info):
                    import os
                    import stat
                    os.chmod(path, stat.S_IWRITE)
                    func(path)

                shutil.rmtree(temp_dir, onerror=onerror)

