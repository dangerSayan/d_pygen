from pathlib import Path
import json
import shutil
import logging
from rich.console import Console
from rich.panel import Panel
from d_pygen.config import save_config
from d_pygen.logger import logger
from d_pygen.config import DEFAULT_CONFIG, CONFIG_FILE, CONFIG_DIR


console = Console()


REGISTRY_FILE = CONFIG_DIR / "registry.json"

PLUGINS_DIR = CONFIG_DIR / "plugins"

TEMPLATES_DIR = CONFIG_DIR / "templates"

CACHE_DIR = CONFIG_DIR / "cache"

LOGS_DIR = CONFIG_DIR / "logs"


DEFAULT_REGISTRY = {
    "version": "1.0.0",
    "initialized": True,
    "plugins": {},
    "templates": {}
}


def create_directory(path: Path):
    path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Created directory: {path}")


def create_config():
    if not CONFIG_FILE.exists():

        config = DEFAULT_CONFIG.copy()

        # Add new defaults
        config["output_dir"] = str(Path.cwd())

        CONFIG_FILE.write_text(
            json.dumps(config, indent=2),
            encoding="utf-8"
        )

        logger.info("Created config.json")


def create_registry():
    if not REGISTRY_FILE.exists():

        REGISTRY_FILE.write_text(
            json.dumps(DEFAULT_REGISTRY, indent=2),
            encoding="utf-8"
        )

        logger.info("Created registry.json")





from d_pygen.config import load_config, save_config





def _shutdown_logging():
    """
    Gracefully shutdown all logging handlers.
    Prevents Windows file lock issues.
    """
    try:
        logging.shutdown()
    except Exception:
        pass


def _safe_reset_config():
    """
    Robust reset of CONFIG_DIR.
    Handles Windows file locks and retry logic.
    """
    try:
        _shutdown_logging()

        if CONFIG_DIR.exists():
            shutil.rmtree(CONFIG_DIR, ignore_errors=False)

        console.print("[green]Configuration reset successfully.[/green]\n")
        return True

    except Exception as e:
        console.print("[red]Reset failed.[/red]")
        logger.error(f"Reset failed: {e}")
        return False


def run_init():

    # --------------------------------------------------
    # Already initialized → show menu
    # --------------------------------------------------

    if CONFIG_DIR.exists():

        console.print("[yellow]d_Pygen is already initialized.[/yellow]\n")

        console.print("1. Reconfigure (recommended)")
        console.print("2. Reset completely")
        console.print("3. Cancel")

        choice = console.input("\nChoose (1/2/3): ").strip()

        # OPTION 3 — CANCEL
        if choice == "3":
            console.print("[red]Initialization cancelled.[/red]")
            return

        # OPTION 2 — RESET
        elif choice == "2":

            console.print(
                "[red]This will delete all configuration, plugins, templates, cache, and logs.[/red]"
            )

            confirm = console.input("Are you sure? (y/n): ").strip().lower()

            if confirm != "y":
                console.print("[red]Reset cancelled.[/red]")
                return

            if not _safe_reset_config():
                return

        # OPTION 1 → Continue to reconfigure

    console.print()
    console.print("[bold cyan]Initializing d_Pygen environment...[/bold cyan]\n")

    try:

        # Create directory structure
        create_directory(CONFIG_DIR)
        create_directory(PLUGINS_DIR)
        create_directory(TEMPLATES_DIR)
        create_directory(CACHE_DIR)
        create_directory(LOGS_DIR)

        create_registry()

        # Load config safely
        try:
            existing = load_config()
        except Exception:
            existing = DEFAULT_CONFIG.copy()

        config = existing.copy()

        console.print("[bold cyan]AI Provider Setup[/bold cyan]\n")

        # ========================================
        # API PROVIDER SETUP
        # ========================================

        console.print("[bold]Cloud API provider[/bold]")
        console.print("1. OpenRouter")
        console.print("2. OpenAI")
        console.print("3. Groq")
        console.print("4. Together AI")
        console.print("5. Skip")

        default_api = existing.get("api_provider", "")

        api_choice = console.input(
            f"\nSelect API provider (1-5) [{default_api or 'Skip'}]: "
        ).strip()

        provider_map = {
            "1": "openrouter",
            "2": "openai",
            "3": "groq",
            "4": "together"
        }

        if api_choice in provider_map:

            provider = provider_map[api_choice]
            config["api_provider"] = provider

            default_key = existing.get("api_key", "")

            api_key = console.input(
                f"Enter API key [{'*' * 8 if default_key else ''}]: "
            ).strip()

            if api_key:
                config["api_key"] = api_key

            default_model = existing.get("api_model", "")

            model = console.input(
                f"Enter model [{default_model}]: "
            ).strip()

            if model:
                config["api_model"] = model

            console.print("[green]✔ API configured[/green]\n")

        # ========================================
        # OLLAMA SETUP
        # ========================================

        console.print("[bold]Ollama setup[/bold]")

        default_ollama = existing.get("ollama_model", "llama3:latest")

        enable_ollama = console.input(
            f"Enable Ollama fallback? (y/n) [{'y' if existing.get('fallback_provider') else 'n'}]: "
        ).strip().lower()

        if enable_ollama == "y":

            config["fallback_provider"] = "ollama"

            model = console.input(
                f"Ollama model [{default_ollama}]: "
            ).strip()

            if model:
                config["ollama_model"] = model

            console.print("[green]✔ Ollama enabled[/green]\n")

        # ========================================
        # PRIORITY SELECTION
        # ========================================

        console.print("[bold]Provider Priority[/bold]\n")
        console.print("1. API → Ollama (recommended)")
        console.print("2. Ollama → API")

        current_priority = existing.get("priority", ["api", "ollama"])

        default_priority = (
            "1" if current_priority == ["api", "ollama"] else "2"
        )

        priority_choice = console.input(
            f"Select priority (1-2) [Default -> {default_priority}]: "
        ).strip()

        if priority_choice == "2":
            config["priority"] = ["ollama", "api"]
        else:
            config["priority"] = ["api", "ollama"]

        # Determine primary provider
        if config["priority"][0] == "api":
            config["provider"] = config.get("api_provider")
        else:
            config["provider"] = "ollama"

        save_config(config)

        console.print(
            Panel(
                "[bold green]✔ d_Pygen initialized successfully[/bold green]\n\n"
                f"Priority order:\n"
                f"  1. {config['priority'][0]}\n"
                f"  2. {config['priority'][1]}",
                border_style="green"
            )
        )

    except Exception as e:

        logger.error("Initialization failed", exc_info=True)

        console.print(
            Panel(
                f"[red]Initialization failed:[/red]\n{str(e)}",
                border_style="red"
            )
        )
