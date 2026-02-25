import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from d_pygen.core.project_detector import detect_project_type
from d_pygen.core.command_runner import run_command
from rich.console import Console

console = Console()

# ============================================================
# HELPER FUNCTIONS
# ============================================================"


def check_tool_exists(tool: str) -> bool:
    """
    Check if a tool exists in PATH.
    Works cross-platform.
    """
    # Fast check using shutil
    if shutil.which(tool):
        return True

    # Fallback check
    try:
        subprocess.run(
            [tool, "--version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return True
    except:
        return False


# ============================================================
# DEPENDENCY FILE DISCOVERY
# ============================================================

def find_dependency_files(project_path: Path):
    """
    Recursively find dependency definition files.
    Supports Python, Node, Rust, Go.
    """
    dependency_files = []

    patterns = {
        "requirements.txt": "python-pip",
        "pyproject.toml": "python-poetry",
        "package.json": "node-npm",
        "Cargo.toml": "rust",
        "go.mod": "go",
    }

    for path in project_path.rglob("*"):
        if path.name in patterns:
            dependency_files.append(
                (patterns[path.name], path.parent)
            )

    return dependency_files


# ============================================================
# PROJECT DETECTION FUNCTIONS
# ============================================================

def detect_project_types(project_path: Path):
    """
    Detect ALL project types recursively.
    Supports MERN, monorepo, microservices.
    """
    return find_dependency_files(project_path)


def detect_project_structure(project_path: Path):
    """
    Detect project definition files and return universal project info.
    """
    mapping = {
        "requirements.txt": {
            "name": "Python project",
            "runtime": ["python", "pip"],
            "type": "python-pip"
        },
        "pyproject.toml": {
            "name": "Python Poetry project",
            "runtime": ["python", "poetry"],
            "type": "python-poetry"
        },
        "package.json": {
            "name": "Node.js project",
            "runtime": ["node", "npm"],
            "type": "node-npm"
        },
        "Cargo.toml": {
            "name": "Rust project",
            "runtime": ["rustc", "cargo"],
            "type": "rust"
        },
        "go.mod": {
            "name": "Go project",
            "runtime": ["go"],
            "type": "go"
        }
    }

    for filename, info in mapping.items():
        file_path = project_path / filename
        if file_path.exists():
            return {
                "name": info["name"],
                "runtime": info["runtime"],
                "type": info["type"],
                "location": filename
            }

    return None


# ============================================================
# DEPENDENCY SCANNER FUNCTIONS
# ============================================================

def scan_dependencies(project_path: Path):
    """
    Scan all dependencies in a project.
    """
    results = []

    project = detect_project_structure(project_path)
    if not project:
        return results

    # Add project info
    results.append({
        "name": project["name"],
        "type": "project",
        "found": True,
        "locations": [project["location"]]
    })

    for runtime in project["runtime"]:

        path = shutil.which(runtime)

        exists = path is not None

        results.append({
            "name": runtime,
            "type": "system",
            "found": exists,
            "locations": [path] if exists else []
        })


    # Scan language-specific dependencies
    project_type = project["type"]

    if project_type.startswith("python"):
        deps = scan_python(project_path)
    elif project_type.startswith("node"):
        deps = scan_node(project_path)
    elif project_type == "rust":
        deps = scan_rust(project_path)
    elif project_type == "go":
        deps = scan_go(project_path)
    else:
        deps = []

    if deps:
        results.extend(deps)

    return results


def scan_python(project_path: Path):
    """
    Scan Python dependencies from requirements.txt.
    """
    req = project_path / "requirements.txt"
    if not req.exists():
        return []

    packages = []
    venv = project_path / ".venv"
    venv_python = (
        venv / "Scripts/python.exe"
        if os.name == "nt"
        else venv / "bin/python"
    )

    for line in req.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        pkg = re.split(r"[<>=]", line)[0].strip()
        locations = []

        # Local venv
        if venv_python.exists():
            try:
                subprocess.run(
                    [str(venv_python), "-c", f"import {pkg}"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=True
                )
                locations.append("local .venv")
            except:
                pass

        # Active env
        try:
            subprocess.run(
                [sys.executable, "-c", f"import {pkg}"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True
            )
            locations.append("active env")
        except:
            pass

        # Global env
        try:
            subprocess.run(
                ["python", "-c", f"import {pkg}"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True
            )
            locations.append("global env")
        except:
            pass

        packages.append({
            "name": pkg,
            "type": "dependency",
            "found": len(locations) > 0,
            "locations": locations
        })

    return packages


def scan_node(project_path: Path):
    """
    Scan Node.js dependencies from package.json.
    """
    package_json = project_path / "package.json"
    if not package_json.exists():
        return []

    data = json.loads(package_json.read_text())
    deps = {}
    deps.update(data.get("dependencies", {}))
    deps.update(data.get("devDependencies", {}))

    packages = []

    for pkg in deps:
        locations = []

        # Local node_modules
        if (project_path / "node_modules" / pkg).exists():
            locations.append("local node_modules")

        # Global npm
        try:
            npm = shutil.which("npm")
            if npm:
                result = subprocess.run(
                    [npm, "root", "-g"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                global_root = Path(result.stdout.strip())
                if (global_root / pkg).exists():
                    locations.append("global npm")
        except:
            pass

        # Active node env
        try:
            subprocess.run(
                ["node", "-e", f"require('{pkg}')"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True
            )
            locations.append("active node env")
        except:
            pass

        packages.append({
            "name": pkg,
            "type": "dependency",
            "found": len(locations) > 0,
            "locations": locations
        })

    return packages


def scan_rust(project_path: Path):
    """
    Scan Rust dependencies from Cargo.toml.
    """
    cargo = project_path / "Cargo.toml"
    if not cargo.exists():
        return []

    packages = []

    try:
        result = subprocess.run(
            ["cargo", "metadata", "--format-version", "1"],
            cwd=project_path,
            capture_output=True,
            text=True
        )

        data = json.loads(result.stdout)

        for pkg in data.get("packages", []):
            locations = []
            if Path(pkg["manifest_path"]).exists():
                locations.append("cargo registry")

            packages.append({
                "name": pkg["name"],
                "type": "dependency",
                "found": True,
                "locations": locations
            })

    except:
        pass

    return packages


def scan_go(project_path: Path):
    """
    Scan Go dependencies from go.mod.
    """
    go_mod = project_path / "go.mod"
    if not go_mod.exists():
        return []

    packages = []

    try:
        result = subprocess.run(
            ["go", "list", "-m", "all"],
            cwd=project_path,
            capture_output=True,
            text=True
        )

        for line in result.stdout.splitlines():
            name = line.split()[0]
            packages.append({
                "name": name,
                "type": "dependency",
                "found": True,
                "locations": ["go module cache"]
            })

    except:
        pass

    return packages


def scan_toolchain(project_path):
    """
    Detect required runtime/toolchain presence.
    """
    project_type = detect_project_type(project_path)
    tools = []

    mapping = {
        "python-pip": ["python", "pip"],
        "python-poetry": ["python", "poetry"],
        "node-npm": ["node", "npm"],
        "node-yarn": ["node", "yarn"],
        "node-pnpm": ["node", "pnpm"],
        "rust": ["rustc", "cargo"],
        "go": ["go"],
    }

    required = mapping.get(project_type, [])

    for tool in required:
        exists = check_tool_exists(tool)
        tools.append({
            "name": tool,
            "type": "system",
            "found": exists,
            "locations": ["PATH"] if exists else []
        })

    return tools


# ============================================================
# DEPENDENCY INSTALLER FUNCTIONS
# ============================================================

def install_dependencies(project_path: Path, mode="local"):
    """
    Install dependencies for a single project.
    """
    project_type = detect_project_type(project_path)

    if project_type == "python-pip":
        if mode == "local":
            venv = project_path / ".venv"
            if not venv.exists():
                subprocess.run(
                    [sys.executable, "-m", "venv", str(venv)],
                    check=True
                )

            python_exec = (
                venv / "Scripts/python.exe"
                if os.name == "nt"
                else venv / "bin/python"
            )

            subprocess.run(
                [str(python_exec), "-m", "pip", "install", "-r", "requirements.txt"],
                cwd=project_path,
                check=True
            )
            return "installed-local"

        elif mode == "global":
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                cwd=project_path,
                check=True
            )
            return "installed-global"

        else:
            return "skipped"

    elif project_type == "python-poetry":
        subprocess.run(
            ["poetry", "install"],
            cwd=project_path,
            check=True
        )
        return "installed-poetry"

    elif project_type == "node-npm":
        run_command(["npm", "install"], project_path)
        return "installed-npm"

    elif project_type == "node-yarn":
        run_command(["yarn", "install"], project_path)
        return "installed-yarn"

    elif project_type == "node-pnpm":
        run_command(["pnpm", "install"], project_path)
        return "installed-pnpm"

    elif project_type == "rust":
        run_command(["cargo", "build"], project_path)
        return "installed-cargo"

    elif project_type == "go":
        run_command(["go", "mod", "tidy"], project_path)
        return "installed-go"

    return "unknown"


def install_all_dependencies(project_path: Path, install_mode):
    """
    Install dependencies for all projects (supports monorepos).
    """
    projects = detect_project_types(project_path)

    if not projects:
        console.print("[yellow]No supported dependency managers found[/yellow]")
        return False

    success_all = True

    for project_type, path in projects:
        console.print(
            f"[bold cyan]Installing dependencies:[/bold cyan] {path}"
        )

        success = install_dependencies_single(
            path,
            project_type,
            install_mode
        )

        if not success:
            success_all = False

    return success_all


def install_dependencies_single(path: Path, project_type, install_mode):
    """
    Install dependencies for a single project type.
    """
    try:
        # Python pip
        if project_type == "python-pip":
            venv = path / ".venv"
            if not venv.exists():
                subprocess.run(
                    [sys.executable, "-m", "venv", str(venv)],
                    check=True
                )

            python_exec = (
                venv / "Scripts/python.exe"
                if os.name == "nt"
                else venv / "bin/python"
            )

            run_command(
                [str(python_exec), "-m", "pip", "install", "-r", "requirements.txt"],
                path
            )
            return True

        # Python poetry
        elif project_type == "python-poetry":
            run_command(["poetry", "install"], path)
            return True

        # Node npm
        elif project_type == "node-npm":
            run_command(["npm", "install"], path)
            return True

        # Rust
        elif project_type == "rust":
            run_command(["cargo", "build"], path)
            return True

        # Go
        elif project_type == "go":
            run_command(["go", "mod", "tidy"], path)
            return True

    except Exception as e:
        console.print(f"[red]Failed installing dependencies in {path}[/red]")
        return False

    return False
