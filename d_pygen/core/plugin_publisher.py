import json
import subprocess
import requests
from pathlib import Path

from rich.console import Console

from d_pygen.core.plugin_validator import validate_local_plugin
from d_pygen.config import CONFIG_DIR

console = Console()

REGISTRY_REPO = "dangerSayan/d_pygen_registry"
REGISTRY_FILE_PATH = "plugins.json"

GITHUB_API = "https://api.github.com"


# ============================================
# Get GitHub repo URL from git config
# ============================================

def get_git_remote():

    try:

        result = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            capture_output=True,
            text=True
        )

        url = result.stdout.strip()

        if url.endswith(".git"):
            url = url[:-4]

        if url.startswith("git@github.com:"):
            url = url.replace("git@github.com:", "https://github.com/")

        return url

    except Exception:

        return None


# ============================================
# Load plugin.json
# ============================================

def load_plugin_metadata():

    plugin_file = Path("plugin.json")

    if not plugin_file.exists():

        console.print("[red]plugin.json not found[/red]")
        return None

    return json.loads(plugin_file.read_text())


# ============================================
# Fetch registry from GitHub
# ============================================

def fetch_registry():

    url = f"https://raw.githubusercontent.com/{REGISTRY_REPO}/main/plugins.json"

    response = requests.get(url)

    if response.status_code != 200:

        console.print("[red]Failed to fetch registry[/red]")
        return None

    return response.json()


# ============================================
# Check duplicate plugin
# ============================================

def check_duplicate(registry, plugin_name):

    return plugin_name in registry


# ============================================
# Publish plugin
# ============================================

def publish_plugin(github_token=None):

    console.print("[cyan]Validating plugin...[/cyan]\n")

    valid = validate_local_plugin(".")

    if not valid:

        console.print("[red]Validation failed[/red]")
        return False

    console.print("[green]✔ Validation successful[/green]\n")

    metadata = load_plugin_metadata()

    if not metadata:

        return False

    plugin_name = metadata["name"]

    repo_url = get_git_remote()

    if not repo_url:

        console.print("[red]Not a git repository[/red]")
        return False

    registry = fetch_registry()

    if registry is None:

        return False

    if check_duplicate(registry, plugin_name):

        console.print("[yellow]Plugin already exists in registry[/yellow]")

        existing = registry[plugin_name]

        if existing.get("version") == metadata.get("version"):

            console.print("[red]Same version already published[/red]")
            return False

        console.print("[cyan]Updating plugin version...[/cyan]")

    registry[plugin_name] = {

        "repo": repo_url,
        "branch": "main",
        "description": metadata.get("description", ""),
        "version": metadata.get("version", "1.0.0")

    }

    console.print("[cyan]Publishing plugin...[/cyan]\n")

    success = update_registry_github(registry, github_token)

    if success:

        console.print("[green]✔ Plugin published successfully[/green]")

    return success


# ============================================
# Update registry via GitHub API
# ============================================

def update_registry_github(registry, token):

    if not token:

        console.print(
            "[yellow]GitHub token required[/yellow]\n"
            "Set using:\n"
            "setx DPYGEN_GITHUB_TOKEN your_token"
        )
        return False

    url = f"{GITHUB_API}/repos/{REGISTRY_REPO}/contents/{REGISTRY_FILE_PATH}"

    headers = {
        "Authorization": f"token {token}"
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:

        console.print("[red]Failed to access registry repo[/red]")
        return False

    sha = response.json()["sha"]

    import base64

    content = base64.b64encode(
        json.dumps(registry, indent=2).encode()
    ).decode()

    data = {

        "message": "Publish plugin via d_Pygen",
        "content": content,
        "sha": sha

    }

    response = requests.put(url, headers=headers, json=data)

    return response.status_code in (200, 201)
