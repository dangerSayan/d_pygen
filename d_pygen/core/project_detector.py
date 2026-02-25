from pathlib import Path


def detect_project_type(project_path: Path):

    # PRIORITY 1: Node (MOST IMPORTANT FIX)
    if (project_path / "package.json").exists():

        if (project_path / "pnpm-lock.yaml").exists():
            return "node-pnpm"

        if (project_path / "yarn.lock").exists():
            return "node-yarn"

        return "node-npm"


    # PRIORITY 2: Python Poetry
    pyproject = project_path / "pyproject.toml"

    if pyproject.exists():
        content = pyproject.read_text(encoding="utf-8")
        if "[tool.poetry]" in content:
            return "python-poetry"


    # PRIORITY 3: Python pip
    if (project_path / "requirements.txt").exists():
        return "python-pip"


    # PRIORITY 4: Rust
    if (project_path / "Cargo.toml").exists():
        return "rust"


    # PRIORITY 5: Go
    if (project_path / "go.mod").exists():
        return "go"


    return "unknown"
