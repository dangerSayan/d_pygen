import shutil
import subprocess
from rich.console import Console
import os
import subprocess

console = Console()

# ============================================================
# TOOL DEFINITIONS
# ============================================================

TOOLCHAIN_MAP = {

    "python": {
        "cmd": "python",
        "name": "Python",
        "install": "https://www.python.org/downloads/"
    },

    "pip": {
        "cmd": "pip",
        "name": "pip",
        "install": "https://pip.pypa.io/en/stable/installation/"
    },

    "node": {
        "cmd": "node",
        "name": "Node.js",
        "install": "https://nodejs.org/"
    },

    "npm": {
        "cmd": "npm",
        "name": "npm",
        "install": "https://nodejs.org/"
    },

    "yarn": {
        "cmd": "yarn",
        "name": "Yarn",
        "install": "https://yarnpkg.com/"
    },

    "pnpm": {
        "cmd": "pnpm",
        "name": "pnpm",
        "install": "https://pnpm.io/installation"
    },

    "rustc": {
        "cmd": "rustc",
        "name": "Rust Compiler",
        "install": "https://rustup.rs/"
    },

    "cargo": {
        "cmd": "cargo",
        "name": "Rust Cargo",
        "install": "https://rustup.rs/"
    },

    "go": {
        "cmd": "go",
        "name": "Go",
        "install": "https://go.dev/dl/"
    },

    "poetry": {
        "cmd": "poetry",
        "name": "Poetry",
        "install": "https://python-poetry.org/docs/"
    }

}

# ============================================================
# PROJECT TYPE → REQUIRED TOOLS
# ============================================================

PROJECT_TOOLCHAIN = {

    "python-pip": ["python", "pip"],
    "python-poetry": ["python", "poetry"],

    "node-npm": ["node", "npm"],
    "node-yarn": ["node", "yarn"],
    "node-pnpm": ["node", "pnpm"],

    "rust": ["rustc", "cargo"],

    "go": ["go"],

}


# ============================================================
# LOW LEVEL CHECK (NO PRINT)
# ============================================================

def tool_exists(tool_key):

    tool = TOOLCHAIN_MAP.get(tool_key)

    if not tool:
        return False

    return shutil.which(tool["cmd"]) is not None

def tool_path(tool_key):

    tool = TOOLCHAIN_MAP.get(tool_key)

    if not tool:
        return None

    return shutil.which(tool["cmd"])



def get_tool_version(tool_key):

    tool = TOOLCHAIN_MAP.get(tool_key)

    if not tool:
        return None

    cmd = tool["cmd"]

    version_flags = ["--version", "-v", "version"]

    for flag in version_flags:

        try:

            # Windows requires shell=True for .cmd tools like npm
            if os.name == "nt":

                result = subprocess.run(
                    f"{cmd} {flag}",
                    capture_output=True,
                    text=True,
                    shell=True
                )

            else:

                result = subprocess.run(
                    [cmd, flag],
                    capture_output=True,
                    text=True,
                    shell=False
                )

            output = (result.stdout or result.stderr).strip()

            if output:

                version = output.split("\n")[0].strip()

                # clean common prefixes
                version = version.replace("npm version", "").strip()

                return version

        except Exception:
            continue

    return None


# ============================================================
# MAIN TOOL CHECK (CONSISTENT RETURN)
# ============================================================

def check_tool(tool_key, show=True):

    tool = TOOLCHAIN_MAP.get(tool_key)

    if not tool:
        return {
            "name": tool_key,
            "found": False,
            "version": None,
            "install": None
        }

    exists = tool_exists(tool_key)

    version = get_tool_version(tool_key) if exists else None

    if show:

        if exists:

            if version:
                console.print(
                    f"[green]✔ {tool['name']}[/green] "
                    f"[dim]({version})[/dim]"
                )
            else:
                console.print(
                    f"[green]✔ {tool['name']}[/green]"
                )


        else:

            console.print(
                f"[red]✘ {tool['name']} NOT installed[/red]"
            )

            console.print(
                f"[yellow]Install from: {tool['install']}[/yellow]\n"
            )

    return {
        "name": tool["name"],
        "found": exists,
        "version": version,
        "install": tool["install"],
        "path": shutil.which(tool["cmd"]) if exists else None
    }


# ============================================================
# PROJECT TOOLCHAIN CHECK (PRINTS ONCE)
# ============================================================

def check_project_toolchain(project_type, show=True):

    required = PROJECT_TOOLCHAIN.get(project_type, [])

    results = []

    if show and required:

        console.print(
            "\n[bold cyan]Checking required toolchain:[/bold cyan]\n"
        )

    for tool in required:

        result = check_tool(tool, show=show)

        results.append(result)

    return results


# ============================================================
# SILENT CHECK (USED BY INSTALLER)
# ============================================================

def is_toolchain_ready(project_type):

    required = PROJECT_TOOLCHAIN.get(project_type, [])

    missing = []

    for tool in required:

        if not tool_exists(tool):
            missing.append(tool)

    return len(missing) == 0, missing
