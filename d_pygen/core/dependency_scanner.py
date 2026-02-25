import json
import os
import sys
import re
import shutil
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# ============================================================
# CACHE
# ============================================================

SCAN_CACHE = {}

def cache_key(project_path: Path):
    return str(project_path.resolve())


def get_cached(project_path: Path):
    return SCAN_CACHE.get(cache_key(project_path))


def set_cache(project_path: Path, data):
    SCAN_CACHE[cache_key(project_path)] = data


# ============================================================
# TOOL DETECTION
# ============================================================

def tool_exists(tool):

    if shutil.which(tool):
        return True

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
# PROJECT DETECTOR (RECURSIVE)
# ============================================================

def detect_projects(root: Path):

    projects = []

    patterns = {
        "requirements.txt": "python-pip",
        "pyproject.toml": "python-poetry",
        "package.json": "node-npm",
        "Cargo.toml": "rust",
        "go.mod": "go"
    }

    for file in root.rglob("*"):

        if file.name in patterns:

            projects.append({
                "type": patterns[file.name],
                "path": file.parent
            })

    return projects


# ============================================================
# PYTHON SCANNER
# ============================================================

def scan_python(project_path):

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

        if venv_python.exists():
            try:
                subprocess.run(
                    [str(venv_python), "-c", f"import {pkg}"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                locations.append("local .venv")
            except:
                pass

        try:
            subprocess.run(
                [sys.executable, "-c", f"import {pkg}"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            locations.append("active env")
        except:
            pass

        try:
            subprocess.run(
                ["python", "-c", f"import {pkg}"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
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


# ============================================================
# NODE SCANNER
# ============================================================

def scan_node(project_path):

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

        if (project_path / "node_modules" / pkg).exists():
            locations.append("local node_modules")

        try:
            npm = shutil.which("npm")

            if npm:
                result = subprocess.run(
                    [npm, "root", "-g"],
                    capture_output=True,
                    text=True
                )

                global_root = Path(result.stdout.strip())

                if (global_root / pkg).exists():
                    locations.append("global npm")

        except:
            pass

        try:
            subprocess.run(
                ["node", "-e", f"require('{pkg}')"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
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


# ============================================================
# RUST SCANNER
# ============================================================

def scan_rust(project_path):

    cargo = project_path / "Cargo.toml"

    if not cargo.exists():
        return []

    return [{
        "name": "Rust dependencies",
        "type": "dependency",
        "found": True,
        "locations": ["cargo registry"]
    }]


# ============================================================
# GO SCANNER
# ============================================================

def scan_go(project_path):

    go_mod = project_path / "go.mod"

    if not go_mod.exists():
        return []

    return [{
        "name": "Go dependencies",
        "type": "dependency",
        "found": True,
        "locations": ["go module cache"]
    }]


# ============================================================
# UNIVERSAL SCANNER
# ============================================================

def scan_project(project):

    path = project["path"]
    type = project["type"]

    cached = get_cached(path)

    if cached:
        return cached

    result = []

    if type.startswith("python"):
        result = scan_python(path)

    elif type.startswith("node"):
        result = scan_node(path)

    elif type == "rust":
        result = scan_rust(path)

    elif type == "go":
        result = scan_go(path)

    set_cache(path, result)

    return result



# ============================================================
# UNIVERSAL RECURSIVE SCAN
# ============================================================

def scan_all(root: Path):

    results = []

    projects = detect_projects(root)

    if not projects:
        return []

    for project in projects:

        path = project["path"]
        type = project["type"]

        # Add project metadata
        results.append({
            "name": f"{type} project",
            "type": "project",
            "found": True,
            "locations": [str(path)]
        })

        # Add runtime
        runtime_map = {
            "python-pip": ["python", "pip"],
            "python-poetry": ["python", "poetry"],
            "node-npm": ["node", "npm"],
            "rust": ["rustc", "cargo"],
            "go": ["go"]
        }

        for tool in runtime_map.get(type, []):

            tool_path = shutil.which(tool)

            exists = tool_path is not None

            results.append({
                "name": tool,
                "type": "system",
                "found": exists,
                "locations": [tool_path] if exists else []
            })


        # Add dependencies
        deps = scan_project(project)

        results.extend(deps)

    return results


