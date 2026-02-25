import subprocess
import sys
import re
import json
import threading
import time
import shutil
import stat

from pathlib import Path
from rich.console import Console

from d_pygen.ui import show_project_structure_from_disk
from d_pygen.logger import logger

from concurrent.futures import ThreadPoolExecutor, as_completed

from d_pygen.core.toolchain import is_toolchain_ready

from d_pygen.core.command_runner import run_command
from d_pygen.core.dependency_manager import detect_project_type, install_all_dependencies



import os
max_workers = min(32, (os.cpu_count() or 4) * 2)

dependency_status = None

dependency_thread = None

console = Console()


def tool_exists(tool: str) -> bool:
    """
    Check if tool exists in system PATH
    """
    return shutil.which(tool) is not None


def check_dependency_locations(project_path: Path) -> dict:
    """
    Returns detailed dependency presence status.

    {
        "local": True/False,
        "active": True/False,
        "global": True/False,
        "any": True/False
    }
    """

    result = {
        "local": False,
        "active": False,
        "global": False,
        "any": False
    }

    req_file = project_path / "requirements.txt"

    if not req_file.exists():
        return result

    # get first valid package
    try:
        first_pkg = None
        with open(req_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    first_pkg = line.split("==")[0].strip()
                    break

        if not first_pkg:
            return result

    except:
        return result


    # -------------------------
    # check local project .venv
    # -------------------------

    venv = project_path / ".venv"

    if os.name == "nt":
        local_python = venv / "Scripts" / "python.exe"
    else:
        local_python = venv / "bin" / "python"

    if local_python.exists():
        try:
            subprocess.run(
                [str(local_python), "-c", f"import {first_pkg}"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True
            )
            result["local"] = True
        except:
            pass


    # -------------------------
    # check active environment
    # -------------------------

    try:
        subprocess.run(
            [sys.executable, "-c", f"import {first_pkg}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )

        if hasattr(sys, "base_prefix") and sys.prefix != sys.base_prefix:
            result["active"] = True
        else:
            result["global"] = True

    except:
        pass


    # -------------------------
    # check global explicitly
    # -------------------------

    try:
        subprocess.run(
            ["python", "-c", f"import {first_pkg}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )
        result["global"] = True
    except:
        pass


    result["any"] = result["local"] or result["active"] or result["global"]

    return result


def scan_all_dependencies(project_path: Path):
    """
    Returns detailed dependency scan result.

    Output format:
    {
        "packages": [
            {
                "name": "fastapi",
                "local": False,
                "active": True,
                "global": True,
                "found": True,
                "location": "active"
            },
            ...
        ],
        "summary": {
            "total": 4,
            "found": 2,
            "missing": 2,
            "complete": False
        }
    }
    """

    requirements = project_path / "requirements.txt"

    if not requirements.exists():
        return None

    packages = []

    with open(requirements, "r", encoding="utf-8") as f:
        for line in f:

            line = line.strip()

            if not line or line.startswith("#"):
                continue

            pkg = re.split(r"[<>=]", line)[0].strip()

            result = {
                "name": pkg,
                "local": False,
                "active": False,
                "global": False,
                "found": False,
                "locations": [],
            }

            # ---------- check local .venv ----------
            venv = project_path / ".venv"

            if os.name == "nt":
                python_exec = venv / "Scripts" / "python.exe"
            else:
                python_exec = venv / "bin" / "python"

            if python_exec.exists():
                try:
                    subprocess.run(
                        [str(python_exec), "-c", f"import {pkg}"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        check=True,
                    )
                    result["local"] = True
                    result["found"] = True
                    if "local" not in result["locations"]:
                        result["locations"].append("local")

                except:
                    pass

            # ---------- check active env ----------
            try:
                subprocess.run(
                    [sys.executable, "-c", f"import {pkg}"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=True,
                )

                if sys.prefix != sys.base_prefix:
                    result["active"] = True
                    result["found"] = True
                    if "active" not in result["locations"]:
                        result["locations"].append("active")


                else:
                    result["global"] = True
                    result["found"] = True
                    if "global" not in result["locations"]:
                        result["locations"].append("global")



            except:
                pass

            # explicit global python check
            try:
                subprocess.run(
                    ["python", "-c", f"import {pkg}"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=True,
                )

                if "global" not in result["locations"]:
                    result["global"] = True
                    result["found"] = True
                    result["locations"].append("global")

            except:
                pass


            packages.append(result)

    total = len(packages)
    found = sum(1 for p in packages if p["found"])
    missing = total - found

    return {
        "packages": packages,
        "summary": {
            "total": total,
            "found": found,
            "missing": missing,
            "complete": missing == 0,
        },
    }



def get_missing_packages(project_path: Path):
    """
    Returns list of missing packages from requirements.txt
    Checks local, active, and global environments
    """

    req_file = project_path / "requirements.txt"

    if not req_file.exists():
        return []

    packages = []

    # extract package names
    with open(req_file, "r", encoding="utf-8") as f:
        for line in f:

            line = line.strip()

            if not line or line.startswith("#"):
                continue

            # remove version specifiers
            pkg = re.split(r"[>=<]", line)[0].strip()

            if pkg:
                packages.append(pkg)

    missing = []

    # determine python executables to test
    interpreters = []

    # local venv
    venv = project_path / ".venv"

    if os.name == "nt":
        local_python = venv / "Scripts" / "python.exe"
    else:
        local_python = venv / "bin" / "python"

    if local_python.exists():
        interpreters.append(str(local_python))

    # active environment
    interpreters.append(sys.executable)

    # global environment
    global_python = sys.base_prefix + "/bin/python"

    if os.name == "nt":
        global_python = sys.base_prefix + "\\python.exe"

    interpreters.append(global_python)

    interpreters = list(set(interpreters))

    # check each package
    for pkg in packages:

        found = False

        for python_exec in interpreters:

            try:

                subprocess.run(
                    [python_exec, "-c", f"import {pkg}"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=True,
                )

                found = True
                break

            except:
                pass

        if not found:
            missing.append(pkg)

    return missing




def resolve_output_path(output_dir: str) -> Path:
    path = Path(output_dir).expanduser().resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_single_file(base_path: Path, file_path: str, content):

    full_path = (base_path / file_path).resolve()

    if not str(full_path).startswith(str(base_path.resolve())):
        raise Exception("Path traversal detected")


    full_path.parent.mkdir(parents=True, exist_ok=True)

    try:

        if isinstance(content, list):
            content = "\n".join(content)

        elif isinstance(content, dict):
            content = json.dumps(content, indent=2)


        elif content is None:
            content = ""

        elif not isinstance(content, str):
            content = str(content)

        # Auto-fix requirements.txt formatting
        if full_path.name == "requirements.txt":
            content = content.replace(",", " ")
            parts = content.split()
            content = "\n".join(parts)

        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)



        logger.info(f"Created file: {full_path}")

        return True

    except Exception as e:

        logger.error(f"Failed writing {file_path}: {str(e)}")

        return False

def safe_rmtree(path: Path, retries: int = 5, delay: float = 0.5):
    """
    Robust Windows-safe directory removal.
    Handles:
    - Read-only files
    - OneDrive locks
    - Temporary file locks
    - Antivirus scanning delays
    """

    def onerror(func, path_str, exc_info):
        try:
            os.chmod(path_str, stat.S_IWRITE)
            func(path_str)
        except Exception:
            pass

    for attempt in range(retries):
        try:
            if path.exists():
                shutil.rmtree(path, onerror=onerror)
            return
        except Exception:
            time.sleep(delay)

    if path.exists():
        raise PermissionError(
            f"Failed to remove directory after {retries} attempts: {path}"
        )



def create_project(plan, output_dir=".", dry_run=False, force=False, install_mode=None):

    if not plan:
        console.print("[red]Invalid project plan[/red]")
        return None, None

    project_name = plan.get("project_name")
    logger.info(f"Creating project: {project_name}")


    if not project_name:
        console.print("[red]Project name missing[/red]")
        return None, None

    

    # inside create_project()
    output_path = resolve_output_path(output_dir)

    output_path.mkdir(parents=True, exist_ok=True)

    base_path = output_path / project_name


    logger.info(f"Creating project at: {base_path}")

    console.print(
        f"[bold green]Project location:[/bold green] {base_path}"
    )


    # DRY RUN MODE
    if dry_run:

        console.print(
            "\n[bold yellow]DRY RUN MODE — No files will be created[/bold yellow]"
        )

        from d_pygen.ui import show_project_structure

        show_project_structure(
            project_name,
            plan.get("folders", []),
            plan.get("files", {}).keys()
        )

        logger.info("Dry run completed")

        console.print(
            "\n[bold green]✔ Dry run complete. No files were created.[/bold green]"
        )

        return base_path



    # --------------------------------------------------
    # Overwrite protection (Improved UX)
    # --------------------------------------------------

    if base_path.exists():

        if force:
            console.print(
                f"[yellow]Project '{project_name}' exists. Overwriting (--force)[/yellow]"
            )
            logger.info("Force overwrite enabled")

            try:
                safe_rmtree(base_path)
            except Exception as e:
                console.print("[red]Overwrite failed[/red]")
                logger.error(str(e))
                return None, None

        else:
            console.print(
                f"[yellow]Project '{project_name}' already exists.[/yellow]"
            )

            console.print("\n[bold cyan]Choose action:[/bold cyan]")
            console.print("1. Overwrite")
            console.print("2. Create new version")
            console.print("3. Cancel")

            choice = console.input("\nEnter choice (1/2/3): ").strip()

            # --------------------------------------------------
            # OPTION 1 — OVERWRITE
            # --------------------------------------------------
            if choice == "1":

                # Prevent deleting while inside project folder
                if base_path.resolve() in Path.cwd().resolve().parents or Path.cwd().resolve() == base_path.resolve():
                    console.print("[red]Cannot overwrite while inside project directory.[/red]")
                    return None, None

                try:
                    safe_rmtree(base_path)
                    logger.info(f"Overwritten project: {project_name}")
                except Exception as e:
                    console.print("[red]Overwrite failed[/red]")
                    logger.error(str(e))
                    return None, None

            # --------------------------------------------------
            # OPTION 2 — CREATE NEW VERSION
            # --------------------------------------------------
            elif choice == "2":

                counter = 1
                while True:
                    new_name = f"{project_name}-{counter}"
                    new_path = output_path / new_name
                    if not new_path.exists():
                        base_path = new_path
                        project_name = new_name
                        console.print(
                            f"[green]Creating project as '{new_name}'[/green]"
                        )
                        logger.info(f"Creating new version: {new_name}")
                        break
                    counter += 1

            # --------------------------------------------------
            # OPTION 3 — CANCEL
            # --------------------------------------------------
            else:
                console.print("[red]Operation cancelled.[/red]")
                logger.info("User cancelled project creation")
                return None, None




    console.print(f"[bold bright_cyan]Creating project:[/bold bright_cyan] {project_name}")

    # Always ensure root exists
    base_path.mkdir(parents=True, exist_ok=True)

    # SAFETY CHECK
    if not base_path.exists():
        raise RuntimeError("Project root directory creation failed")




    # --------------------------------------------------
    # Create folders
    # --------------------------------------------------

    for folder in plan.get("folders", []):

        folder_path = base_path / folder
        folder_path.mkdir(parents=True, exist_ok=True)

    # --------------------------------------------------
    # Create files in parallel
    # --------------------------------------------------

    files = plan.get("files", {})

    file_count = len(files)

    console.print(
        f"[cyan]Creating {file_count} files in parallel using {max_workers} threads...[/cyan]"
    )


    with ThreadPoolExecutor(max_workers=max_workers) as executor:

        futures = [

            executor.submit(
                write_single_file,
                base_path,
                file_path,
                content
            )

            for file_path, content in files.items()

        ]

        for future in as_completed(futures):

            try:

                result = future.result()

                if not result:

                    console.print(
                        "[red]File creation failed[/red]"
                    )

            except Exception as e:

                logger.error(f"Thread crashed: {str(e)}")

                console.print(
                    "[red]File creation thread crashed[/red]"
                )




    # --------------------------------------------------
    # Show visual project structure (ONLY ONCE)
    # --------------------------------------------------

    show_project_structure_from_disk(base_path)


    project_type = plan.get("project_type")

    detected_type = detect_project_type(base_path)


    # Filesystem detection takes priority
    if detected_type and detected_type != "unknown":
        project_type = detected_type

    # fallback safety
    if not project_type:
        project_type = "unknown"



    # --------------------------------------------------
    # Install dependencies (PLAN-AWARE DETECTION)
    # --------------------------------------------------

    if not dry_run:

        

        if install_mode is None:

            console.print("\n[bold cyan]Install dependencies?[/bold cyan]")

            if project_type in ["python-pip", "python"]:

                console.print("1. Local (.venv)")
                console.print("2. Global")
                console.print("3. Skip")

            elif project_type in ["node-npm", "node", "nodejs"]:

                console.print("1. Local (node_modules)")
                console.print("2. Global")
                console.print("3. Skip")

            elif project_type == "rust":

                console.print("1. Local (cargo build)")
                console.print("2. Global (cargo install)")
                console.print("3. Skip")

            elif project_type == "go":

                console.print("1. Local (go mod tidy)")
                console.print("2. Global")
                console.print("3. Skip")

            else:

                console.print("1. Local install")
                console.print("2. Global")
                console.print("3. Skip")

            choice = console.input("\nChoice (1/2/3): ").strip()

            if choice == "1":
                install_mode = "local"
            elif choice == "2":
                install_mode = "global"
            else:
                install_mode = "none"


        if install_mode != "none":

            install_dependencies_background(base_path, install_mode)

        else:

            global dependency_status
            dependency_status = "skipped"





    return base_path, install_mode





def install_dependencies(project_path, install_mode, skip_toolchain_check=False):

    global dependency_status

    dependency_status = "installing"

    logger.info(f"Installing dependencies for {project_path}")

    console.print()

    try:

        project_type = detect_project_type(project_path)

        # Check toolchain BEFORE installing dependencies
        ready, missing = is_toolchain_ready(project_type)

        if not ready:

            

            dependency_status = "failed"

            return

        # Toolchain OK → install dependencies
        success = install_all_dependencies(project_path, install_mode)

        if success:

            console.print(
                "[bold green]✔ Dependencies installed successfully[/bold green]"
            )

            dependency_status = "installed"

        else:

            console.print(
                "[bold red]✘ Dependency installation failed[/bold red]"
            )

            dependency_status = "failed"

    except Exception as e:

        logger.error(str(e))

        console.print(
            "[bold red]✘ Dependency installation crashed[/bold red]"
        )

        dependency_status = "failed"


def install_dependencies_background(project_path, install_mode):

    global dependency_thread

    console.print(
        "[yellow]Installing dependencies in background...[/yellow]"
    )

    dependency_thread = threading.Thread(
        target=install_dependencies,
        args=(project_path, install_mode, False),
        daemon=True   # prevents blocking exit
    )


    dependency_thread.start()


def wait_for_dependency_install():

    global dependency_thread
    global dependency_status

    if dependency_thread:

        console.print(
            "[dim]Finalizing dependency installation...[/dim]"
        )

        dependency_thread.join()

    return dependency_status


