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
        config["output_dir"] = DEFAULT_CONFIG["output_dir"]

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

    if CONFIG_FILE.exists():

        console.print("[yellow]d_Pygen is already initialized.[/yellow]\n")

        console.print("1. Reconfigure (recommended)")
        console.print("2. Reset completely")
        console.print("3. Cancel")

        choice = console.input("\nChoose (1/2/3): ").strip()

        if choice == "3":
            console.print("[red]Initialization cancelled.[/red]")
            return

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


    console.print()
    console.print("[bold cyan]Initializing d_Pygen environment...[/bold cyan]\n")

    try:

        create_directory(CONFIG_DIR)
        create_directory(PLUGINS_DIR)
        create_directory(TEMPLATES_DIR)
        create_directory(CACHE_DIR)
        create_directory(LOGS_DIR)

        create_registry()
        create_config()

        try:
            existing = load_config()
        except Exception:
            existing = DEFAULT_CONFIG.copy()

        config = existing.copy()

        console.print("[bold cyan]AI Provider Setup[/bold cyan]\n")

        # =====================================================
        # PROVIDER SELECTION
        # =====================================================

        console.print("[bold]Cloud API provider[/bold]\n")

        console.print("1. OpenRouter")
        console.print("2. OpenAI")
        console.print("3. Groq")
        console.print("4. Together AI")
        console.print("5. Gemini")
        console.print("6. Custom provider (OpenAI-compatible)")
        console.print("7. Skip")

        default_api = existing.get("api_provider") or "Skip"

        api_choice = console.input(
            f"\nSelect provider (1-7) [{default_api}]: "
        ).strip()


        provider_map = {
            "1": ("openrouter", None),
            "2": ("openai", None),
            "3": ("groq", None),
            "4": ("together", None),
            "5": ("gemini", None),
        }


        # =====================================================
        # STANDARD PROVIDERS
        # =====================================================

        if api_choice in provider_map:

            provider, base_url = provider_map[api_choice]

            config["api_provider"] = provider

            if base_url:
                config["base_url"] = base_url


            api_key = console.input("Enter API key: ").strip()

            if api_key:
                config["api_key"] = api_key


            model = console.input("Enter model name: ").strip()

            if model:
                config["api_model"] = model


            console.print(f"[green]✔ {provider} configured[/green]\n")


        # =====================================================
        # CUSTOM PROVIDER
        # =====================================================

        elif api_choice == "6":

            provider = console.input(
                "Provider name (example: deepseek, mistral, anthropic): "
            ).strip().lower()

            base_url = console.input(
                "Provider base_url (example: https://api.deepseek.com/v1): "
            ).strip()

            if not provider or not base_url:

                console.print(
                    "[red]Provider name and base_url are required[/red]"
                )

                return


            config["api_provider"] = provider
            config["base_url"] = base_url


            api_key = console.input("API key: ").strip()

            if api_key:
                config["api_key"] = api_key


            model = console.input("Model name: ").strip()

            if model:
                config["api_model"] = model


            console.print(
                f"[green]✔ Custom provider '{provider}' configured[/green]\n"
            )


        # =====================================================
        # SKIP
        # =====================================================

        elif api_choice == "7":

            console.print("[yellow]Skipped API setup[/yellow]\n")


        # =====================================================
        # OLLAMA SETUP
        # =====================================================

        console.print("[bold]Ollama fallback[/bold]\n")

        enable_ollama = console.input(
            "Enable Ollama fallback? (y/n): "
        ).strip().lower()

        if enable_ollama == "y":

            config["fallback_provider"] = "ollama"

            model = console.input(
                "Ollama model [llama3:latest]: "
            ).strip()

            config["ollama_model"] = model or "llama3:latest"

            console.print("[green]✔ Ollama enabled[/green]\n")


        # =====================================================
        # PRIORITY
        # =====================================================

        console.print("[bold]Provider priority[/bold]\n")

        console.print("1. API → Ollama")
        console.print("2. Ollama → API")

        choice = console.input("Select (1-2): ").strip()

        if choice == "2":

            config["priority"] = ["ollama", "api"]
            config["provider"] = "ollama"

        else:

            config["priority"] = ["api", "ollama"]
            config["provider"] = config.get("api_provider")


        save_config(config)


        console.print(
            Panel(
                "[bold green]✔ Initialization complete[/bold green]",
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
