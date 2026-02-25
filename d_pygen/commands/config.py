import json
import os
import subprocess
from rich.console import Console
from rich.panel import Panel

from d_pygen.config import CONFIG_FILE, load_config, save_config, DEFAULT_CONFIG

console = Console()

# ============================================
# SHOW CONFIG
# ============================================

def config_show():

    config = load_config()

    console.print(
        Panel(
            json.dumps(config, indent=2),
            title="d_Pygen Configuration",
            border_style="cyan"
        )
    )


# ============================================
# SET CONFIG VALUE
# ============================================

def config_set(key, value):

    config = load_config()

    if key not in DEFAULT_CONFIG:
        console.print(f"[red]Invalid config key:[/red] {key}")
        return

    config[key] = value

    save_config(config)

    console.print(
        f"[green]✔ Config updated:[/green] {key} = {value}"
    )


# ============================================
# RESET CONFIG
# ============================================

def config_reset():

    save_config(DEFAULT_CONFIG.copy())

    console.print(
        "[green]✔ Config reset to defaults[/green]"
    )


# ============================================
# EDIT CONFIG FILE
# ============================================

def config_edit():

    editor = os.getenv("EDITOR")

    if not editor:

        if os.name == "nt":
            editor = "notepad"
        else:
            editor = "nano"

    subprocess.run([editor, str(CONFIG_FILE)])





def config_wizard():

    console.print()
    console.print(
        Panel(
            "[bold cyan]d_Pygen Config Wizard[/bold cyan]\n"
            "Interactive configuration setup",
            border_style="cyan"
        )
    )

    config = load_config()

    # -----------------------
    # API Provider
    # -----------------------

    console.print("\n[bold]Select API Provider:[/bold]")

    console.print("1. OpenRouter")
    console.print("2. OpenAI")
    console.print("3. Groq")
    console.print("4. Together")
    console.print("5. None")

    choice = console.input("\nChoice (1-5): ").strip()

    provider_map = {
        "1": "openrouter",
        "2": "openai",
        "3": "groq",
        "4": "together"
    }

    if choice in provider_map:

        provider = provider_map[choice]

        config["api_provider"] = provider

        key = console.input(f"{provider} API key: ").strip()

        if key:
            config["api_key"] = key

        model = console.input("Model name: ").strip()

        if model:
            config["api_model"] = model


        console.print("[green]✔ API configured[/green]")

    # -----------------------
    # Ollama
    # -----------------------

    console.print("\n[bold]Ollama setup:[/bold]")

    enable = console.input("Enable Ollama fallback? (y/n): ").strip().lower()

    if enable == "y":

        config["fallback_provider"] = "ollama"

        model = console.input("Ollama model (default llama3): ").strip()

        config["ollama_model"] = model or "llama3"

        console.print("[green]✔ Ollama configured[/green]")

    else:

        config["fallback_provider"] = None

    # -----------------------
    # Priority
    # -----------------------

    console.print("\n[bold]Provider priority:[/bold]")

    console.print("1. API → Ollama")
    console.print("2. Ollama → API")

    priority = console.input("Choice (1-2): ").strip()

    if priority == "2":

        config["priority"] = ["ollama", "api"]
        config["provider"] = "ollama"

    else:

        config["priority"] = ["api", "ollama"]
        config["provider"] = config.get("api_provider")

    save_config(config)

    console.print(
        Panel(
            "[bold green]Configuration saved successfully[/bold green]",
            border_style="green"
        )
    )

