import json
import shutil
from pathlib import Path
import tempfile
import zipfile
import requests

import threading
import time

from rich.console import Console

from d_pygen.logger import logger
from d_pygen.core.plugin_validator import validate_github_plugin

from d_pygen.config import (
    CONFIG_DIR,
    INSTALLED_PLUGINS_FILE,
    PLUGIN_REGISTRY_FILE
)

console = Console()



# Prevent concurrent installsf
INSTALL_LOCK = threading.Lock()



PLUGINS_DIR = CONFIG_DIR / "plugins"
TEMPLATES_DIR = CONFIG_DIR / "templates"



# Example plugin registry source (local for now)
PLUGIN_SOURCE_DIR = CONFIG_DIR / "plugin_source"

PLUGIN_REGISTRY_URL = "https://raw.githubusercontent.com/dangerSayan/d_pygen_registry/main/plugins.json"

# Ensure required directories exist
PLUGINS_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
PLUGIN_SOURCE_DIR.mkdir(parents=True, exist_ok=True)

# Ensure registry file exists
if not PLUGIN_REGISTRY_FILE.exists():
    PLUGIN_REGISTRY_FILE.write_text("{}")

# Ensure installed file exists
if not INSTALLED_PLUGINS_FILE.exists():
    INSTALLED_PLUGINS_FILE.write_text("{}")




REGISTRY_MAX_AGE = 60 * 60 * 24  # 24 hours

import socket

def has_internet():

    try:

        socket.create_connection(("8.8.8.8", 53), timeout=3)

        return True

    except OSError:

        return False
    


def load_installed_plugins():

    try:
        return json.loads(
            INSTALLED_PLUGINS_FILE.read_text()
        )
    except Exception:

        # reset corrupted file
        INSTALLED_PLUGINS_FILE.write_text("{}")
        return {}



def save_installed_plugins(data):

    INSTALLED_PLUGINS_FILE.write_text(
        json.dumps(data, indent=2)
    )


# ============================================
# VALIDATE INSTALLED PLUGINS HEALTH
# ============================================

def validate_installed_plugins():

    installed = load_installed_plugins()

    broken = []

    for plugin in installed:

        plugin_path = PLUGINS_DIR / plugin

        if not plugin_path.exists():

            broken.append(plugin)

    return broken


# ============================================
# AUTO FIX BROKEN PLUGINS
# ============================================

def fix_broken_plugins():

    broken = validate_installed_plugins()

    if not broken:
        return

    installed = load_installed_plugins()

    for plugin in broken:

        logger.warning(f"Fixing broken plugin: {plugin}")

        installed.pop(plugin, None)

    save_installed_plugins(installed)

    console.print(
        f"[yellow]Fixed {len(broken)} broken plugin(s)[/yellow]"
    )




def install_plugin_smart(plugin_name: str):

    # Ensure registry exists
    if not PLUGIN_REGISTRY_FILE.exists():
        update_plugin_registry(silent=True)

    console.print(f"[cyan]Installing plugin '{plugin_name}'...[/cyan]")

    internet = has_internet()

    # Step 1: Try GitHub if internet available
    if internet:

        console.print("[dim]Internet detected → using GitHub[/dim]")

        success = install_plugin_github(plugin_name)

        if success:
            return True

        console.print("[yellow]GitHub install failed, trying local...[/yellow]")

    else:

        console.print("[yellow]No internet connection[/yellow]")


    # Step 2: Try local fallback
    local_path = PLUGIN_SOURCE_DIR / plugin_name

    if local_path.exists():

        console.print("[dim]Using local plugin[/dim]")

        return install_plugin(plugin_name)


    # Step 3: Final failure
    console.print(
        f"[red]✘ Cannot install plugin '{plugin_name}'[/red]"
    )

    if internet:

        console.print(
            "[yellow]Reason: Plugin not found in registry or GitHub, "
            "and no local plugin available[/yellow]"
        )

    else:

        console.print(
            "[yellow]Reason: No internet connection and no local plugin available[/yellow]"
        )

    return False



def is_registry_outdated():

    if not PLUGIN_REGISTRY_FILE.exists():
        return True

    try:

        last_modified = PLUGIN_REGISTRY_FILE.stat().st_mtime

        age = time.time() - last_modified

        return age > REGISTRY_MAX_AGE

    except Exception:

        return True



def auto_update_registry_background():

    def worker():

        try:

            if is_registry_outdated():

                logger.info("Auto-updating plugin registry")

                update_plugin_registry(silent=True)

        except Exception as e:

            logger.debug(f"Registry auto-update failed: {e}")

    thread = threading.Thread(
        target=worker,
        daemon=True
    )

    thread.start()




def update_plugin_registry(silent=False):

    if not silent:
        console.print("[cyan]Updating plugin registry...[/cyan]")

    try:

        response = requests.get(
            PLUGIN_REGISTRY_URL,
            timeout=15
        )

        if response.status_code != 200:

            logger.error(f"Registry fetch failed: HTTP {response.status_code}")

            if not silent:
                console.print("[red]Failed to fetch registry[/red]")

            return False


        # Parse JSON FIRST (important)
        try:
            registry = response.json()
        except Exception as e:

            logger.error(f"Invalid registry JSON: {e}")

            if not silent:
                console.print("[red]Registry JSON invalid[/red]")

            return False


        # Validate registry content
        if not isinstance(registry, dict) or len(registry) == 0:

            logger.error("Registry is empty or invalid")

            if not silent:
                console.print("[red]Registry is empty[/red]")

            return False


        # Save registry safely
        PLUGIN_REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)

        PLUGIN_REGISTRY_FILE.write_text(
            json.dumps(registry, indent=2),
            encoding="utf-8"
        )


        logger.info(f"Registry saved with {len(registry)} plugins")

        if not silent:
            console.print(
                f"[green]✔ Plugin registry updated ({len(registry)} plugins)[/green]"
            )

        return True


    except Exception as e:

        logger.error(f"Registry update failed: {e}", exc_info=True)

        if not silent:
            console.print(
                f"[red]Registry update failed:[/red] {e}"
            )

        return False




def install_plugin(plugin_name: str):

    with INSTALL_LOCK:

        console.print("[cyan]Installing plugin locally...[/cyan]")

        source = PLUGIN_SOURCE_DIR / plugin_name

        if not source.exists():

            console.print(
                f"[red]Local plugin '{plugin_name}' not found in {PLUGIN_SOURCE_DIR}[/red]"
            )

            return False

        destination = PLUGINS_DIR / plugin_name

        if destination.exists():

            console.print("[yellow]Plugin already installed[/yellow]")

            return True

        shutil.copytree(source, destination)

        # install templates
        templates_src = source / "templates"

        if templates_src.exists():

            for template in templates_src.iterdir():

                dest_template = TEMPLATES_DIR / template.name

                if dest_template.exists():
                    shutil.rmtree(dest_template)

                shutil.copytree(template, dest_template)

        installed = load_installed_plugins()

        # Try to get version from registry
        registry = fetch_registry()

        version = "unknown"

        if plugin_name in registry:
            version = registry[plugin_name].get("version", "unknown")

        installed[plugin_name] = {
            "installed": True,
            "source": "local",
            "version": version
        }

        save_installed_plugins(installed)



        console.print(
            f"[green]✔ Plugin '{plugin_name}' installed locally[/green]"
        )

        return True



def uninstall_plugin(plugin_name: str):

    plugin_path = PLUGINS_DIR / plugin_name
    cache_path = PLUGIN_SOURCE_DIR / plugin_name

    installed = load_installed_plugins()

    if plugin_name not in installed:
        console.print(f"[yellow]Plugin '{plugin_name}' not registered[/yellow]")
        return False

    # Remove installed plugin
    if plugin_path.exists():
        shutil.rmtree(plugin_path)
        console.print("[green]✔ Plugin folder removed[/green]")

    

    installed.pop(plugin_name)
    save_installed_plugins(installed)

    console.print(f"[green]✔ Plugin '{plugin_name}' uninstalled[/green]")

    return True





def list_plugins():

    installed = load_installed_plugins()

    valid_plugins = []

    for name in installed:

        if (PLUGINS_DIR / name).exists():

            valid_plugins.append(name)

    return valid_plugins








def install_plugin_github(plugin_name: str):

    zip_path = None


    if not shutil.which("git"):
        console.print("[bold red]✘ Git is required to install plugins from GitHub.[/bold red]")
        console.print("[yellow]Install Git from: https://git-scm.com/downloads[/yellow]")
        return False

    with INSTALL_LOCK:

        logger.info(f"Installing plugin from GitHub: {plugin_name}")

        console.print("[cyan]Fetching plugin registry...[/cyan]")

        try:

            registry = fetch_registry()

            if not registry:

                console.print("[red]Failed to fetch registry[/red]")
                return False

            if plugin_name not in registry:

                console.print("[red]Plugin not found in registry[/red]")
                return False

            entry = registry[plugin_name]

            if isinstance(entry, str):
                repo = entry
                branch = "main"
                latest_version = "unknown"
            else:
                repo = entry.get("repo")
                branch = entry.get("branch", "main")
                latest_version = entry.get("version", "unknown")

            branch = registry[plugin_name].get("branch", "main")

            # ============================================
            # SKIP INSTALL IF SAME VERSION ALREADY INSTALLED
            # ============================================

            installed = load_installed_plugins()

            latest_version = registry[plugin_name].get("version", "unknown")

            if plugin_name in installed:

                installed_version = installed[plugin_name].get("version", "unknown")

                if installed_version == latest_version:

                    console.print("[green]Plugin already up-to-date[/green]")
                    return True


            # ============================================================
            # VALIDATE PLUGIN BEFORE INSTALL
            # ============================================================

            console.print("[cyan]Validating plugin...[/cyan]")

            valid = validate_github_plugin(repo, branch)

            if not valid:

                console.print(
                    "[bold red]Plugin validation failed. Installation aborted.[/bold red]"
                )

                return False


            console.print("[green]✔ Plugin validation passed[/green]")

            zip_url = f"{repo}/archive/refs/heads/{branch}.zip"

            console.print("[cyan]Downloading plugin from GitHub...[/cyan]")

            response = requests.get(zip_url, timeout=60)

            if response.status_code != 200:

                console.print("[red]Download failed[/red]")
                return False

            with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:

                tmp.write(response.content)

                zip_path = tmp.name

            extract_dir = tempfile.mkdtemp()

            with zipfile.ZipFile(zip_path, "r") as zip_ref:

                zip_ref.extractall(extract_dir)

            extracted_folder = next(Path(extract_dir).glob("*"))

            destination = PLUGINS_DIR / plugin_name

            if destination.exists():

                shutil.rmtree(destination)

            shutil.copytree(extracted_folder, destination)

            templates_src = destination / "templates"

            if templates_src.exists():

                for template in templates_src.iterdir():

                    dest_template = TEMPLATES_DIR / template.name

                    if dest_template.exists():

                        shutil.rmtree(dest_template)

                    shutil.copytree(template, dest_template)

            installed = load_installed_plugins()

            installed[plugin_name] = {
                "installed": True,
                "source": "github",
                "repo": repo,
                "branch": branch,
                "version": registry[plugin_name].get("version", "unknown")
            }

            save_installed_plugins(installed)


            console.print(
                f"[green]✔ Plugin '{plugin_name}' installed from GitHub[/green]"
            )
            # cache plugin for offline use
            local_cache = PLUGIN_SOURCE_DIR / plugin_name

            if local_cache.exists():
                shutil.rmtree(local_cache)

            shutil.copytree(destination, local_cache)

            return True

        except Exception as e:
            logger.error("GitHub install failed", exc_info=True)
            console.print(
                f"[bold red]✘ Plugin install failed[/bold red]\n"
                f"[yellow]Reason:[/yellow] {str(e)}"
            )
            return False


        finally:
            if zip_path:
                try:
                    Path(zip_path).unlink(missing_ok=True)
                except:
                    pass



    









def fetch_registry():

    if (
        not PLUGIN_REGISTRY_FILE.exists()
        or PLUGIN_REGISTRY_FILE.stat().st_size == 0
    ):
        logger.info("Registry missing or empty, downloading")
        success = update_plugin_registry(silent=True)
        if not success:
            return {}

    try:
        registry = json.loads(
            PLUGIN_REGISTRY_FILE.read_text(encoding="utf-8")
        )

        # Ensure registry is valid format
        if not isinstance(registry, dict):
            raise ValueError("Registry not a dictionary")

        # Validate entries
        for name, data in registry.items():
            if not isinstance(data, dict):
                raise ValueError("Invalid registry format")

        return registry

    except Exception:

        logger.warning("Registry corrupted or invalid, re-downloading")

        update_plugin_registry(silent=True)

        try:
            return json.loads(
                PLUGIN_REGISTRY_FILE.read_text(encoding="utf-8")
            )
        except:
            return {}








def search_plugins():

    registry = fetch_registry()

    if not registry:
        return []

    plugins = []

    for name, data in registry.items():

        if isinstance(data, str):
            description = ""
        elif isinstance(data, dict):
            description = data.get("description", "")
        else:
            description = ""

        plugins.append({
            "name": name,
            "description": description
        })

    return plugins


def get_plugin_info(plugin_name):

    registry = fetch_registry()

    if plugin_name not in registry:
        return None

    return registry[plugin_name]


# ============================================================
# Plugin Update System
# ============================================================

def update_plugin(plugin_name: str):
    """
    Update a single plugin from its original source.
    """

    installed = load_installed_plugins()

    plugin = installed.get(plugin_name)

    if not plugin:
        console.print(f"[red]Plugin '{plugin_name}' is not installed[/red]")
        return False

    source = plugin.get("source")

    console.print(f"[cyan]Updating plugin '{plugin_name}'...[/cyan]")

    try:

        if source == "github":
            success = install_plugin_github(plugin_name)

        elif source == "local":
            success = install_plugin(plugin_name)

        else:
            console.print("[red]Unknown plugin source[/red]")
            return False

        if success:
            console.print(f"[green]✔ Plugin '{plugin_name}' updated[/green]")
            return True

        return False

    except Exception as e:

        logger.error("Plugin update failed", exc_info=True)

        console.print(f"[red]Update failed:[/red] {str(e)}")

        return False


def update_all_plugins():
    """
    Update all installed plugins.
    """

    plugins = load_installed_plugins()

    if not plugins:
        console.print("[yellow]No plugins installed[/yellow]")
        return

    console.print(f"[cyan]Updating {len(plugins)} plugins...[/cyan]")

    success_count = 0

    for plugin_name in plugins:

        success = update_plugin(plugin_name)

        if success:
            success_count += 1

    console.print(
        f"[green]✔ Updated {success_count}/{len(plugins)} plugins[/green]"
    )


def get_installed_plugins():
    return load_installed_plugins()


def check_outdated_plugins():

    console.print("[cyan]Checking for plugin updates...[/cyan]\n")

    installed = get_installed_plugins()

    if not installed:
        console.print("[yellow]No plugins installed[/yellow]")
        return []

    remote_registry = fetch_registry()

    outdated = []

    for name, info in installed.items():

        if name not in remote_registry:
            continue

        installed_version = info.get("version", "unknown")

        latest_version = remote_registry[name].get("version", "unknown")

        if installed_version == "unknown":
            continue

        if installed_version != latest_version:



            outdated.append({
                "name": name,
                "installed": installed_version,
                "latest": latest_version
            })

    return outdated


def upgrade_plugins():

    console.print("[cyan]Checking for outdated plugins...[/cyan]\n")

    outdated = check_outdated_plugins()

    if not outdated:

        console.print("[green]All plugins already up to date[/green]")
        return True

    console.print(f"[yellow]Upgrading {len(outdated)} plugin(s)...[/yellow]\n")

    success_count = 0

    for plugin in outdated:

        name = plugin["name"]

        console.print(f"[cyan]Upgrading {name}...[/cyan]")

        success = update_plugin(name)

        if success:

            console.print(f"[green]✔ {name} upgraded[/green]")
            success_count += 1

        else:

            console.print(f"[red]✗ {name} failed to upgrade[/red]")

    console.print()

    console.print(
        f"[bold green]Upgrade complete: {success_count}/{len(outdated)} successful[/bold green]"
    )

    return True


def marketplace_plugins():
    """
    Show plugin marketplace (professional display)
    """

    console.print("\n[bold bright_cyan]d_Pygen Plugin Marketplace[/bold bright_cyan]\n")

    registry = fetch_registry()

    if not registry:
        console.print("[red]Marketplace unavailable[/red]")
        return []

    plugins = []

    for name, data in registry.items():

        # Support OLD registry format (string repo only)
        if isinstance(data, str):
            description = "No description"
            repo = data
            version = "unknown"

        # NEW format (dict)
        elif isinstance(data, dict):
            description = data.get("description", "No description")
            repo = data.get("repo", "")
            version = data.get("version", "unknown")

        else:
            continue

        plugins.append({
            "name": name,
            "description": description,
            "repo": repo,
            "version": version
        })

    plugins.sort(key=lambda x: x["name"])

    for plugin in plugins:

        console.print(
            f"[bold green]{plugin['name']}[/bold green]\n"
            f"   {plugin['description']}\n"
            f"   version: {plugin['version']}\n"
        )

    console.print(f"[dim]{len(plugins)} plugins available[/dim]\n")

    return plugins

# ============================================
# CLEAR PLUGIN CACHE
# ============================================

def clear_plugin_cache(plugin_name=None):

    if plugin_name:
        cache_path = PLUGIN_SOURCE_DIR / plugin_name

        if cache_path.exists():
            shutil.rmtree(cache_path)
            console.print(f"[green]✔ Cache cleared for '{plugin_name}'[/green]")
        else:
            console.print("[yellow]No cache found[/yellow]")

        return

    # clear all cache
    if not PLUGIN_SOURCE_DIR.exists():
        console.print("[yellow]No cache directory found[/yellow]")
        return

    count = 0

    for item in PLUGIN_SOURCE_DIR.iterdir():

        if item.is_dir():
            shutil.rmtree(item)
            count += 1

    console.print(f"[green]✔ Cleared cache for {count} plugin(s)[/green]")


# ============================================
# PLUGIN CACHE INFO
# ============================================

def get_plugin_cache_info():

    if not PLUGIN_SOURCE_DIR.exists():

        return {
            "location": str(PLUGIN_SOURCE_DIR),
            "plugins": 0,
            "size_bytes": 0,
            "breakdown": {}
        }

    total_size = 0
    plugin_count = 0
    breakdown = {}

    for plugin_dir in PLUGIN_SOURCE_DIR.iterdir():

        if not plugin_dir.is_dir():
            continue

        plugin_size = 0

        for file in plugin_dir.rglob("*"):

            if file.is_file():
                plugin_size += file.stat().st_size

        breakdown[plugin_dir.name] = plugin_size

        total_size += plugin_size
        plugin_count += 1

    return {
        "location": str(PLUGIN_SOURCE_DIR),
        "plugins": plugin_count,
        "size_bytes": total_size,
        "breakdown": breakdown
    }
