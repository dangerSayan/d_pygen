import os
import sys
import shutil
import subprocess
import requests

from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from d_pygen.cache import CACHE_DIR
from d_pygen.config import load_config, CONFIG_FILE


console = Console()


# ============================================================
# HELPERS
# ============================================================

def success(msg):
    console.print(f"[green]✔ {msg}[/green]")


def warn(msg):
    console.print(f"[yellow]⚠ {msg}[/yellow]")


def fail(msg):
    console.print(f"[red]✘ {msg}[/red]")


def info(msg):
    console.print(f"[cyan]{msg}[/cyan]")


# ============================================================
# PYTHON CHECK
# ============================================================

def check_python():

    version = sys.version_info

    if version.major >= 3 and version.minor >= 8:

        success(f"Python {version.major}.{version.minor}.{version.micro}")

        return True

    fail("Python 3.8+ required")

    return False


# ============================================================
# CONFIG CHECK
# ============================================================

def check_config():

    if CONFIG_FILE.exists():

        success(f"Config file found")
        info(f"Location: {CONFIG_FILE}")

        try:

            config = load_config()

            provider = config.get("provider", "auto")

            info(f"Provider: {provider}")

            return True

        except Exception as e:

            fail(f"Config invalid: {e}")
            return False

    warn("Config file not initialized")

    info("Run: d_Pygen init")

    return False


# ============================================================
# CACHE CHECK
# ============================================================

def check_cache():

    try:

        CACHE_DIR.mkdir(parents=True, exist_ok=True)

        test = CACHE_DIR / ".doctor_test"

        test.write_text("ok")
        test.unlink()

        success("Cache writable")
        info(f"Location: {CACHE_DIR}")

        return True

    except Exception:

        fail("Cache not writable")
        info("Fix permissions")

        return False


# ============================================================
# API KEY CHECK (CONFIG + ENV)
# ============================================================

def check_api():

    config = load_config()

    config_key = config.get("api_key")

    env_keys = {
        "OPENROUTER_API_KEY": os.getenv("OPENROUTER_API_KEY"),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "GROQ_API_KEY": os.getenv("GROQ_API_KEY"),
        "TOGETHER_API_KEY": os.getenv("TOGETHER_API_KEY"),
    }

    # Priority 1: config.json
    if config_key:

        success("API key configured")
        info("Source: config.json")
        return True

    # Priority 2: environment variables
    for name, value in env_keys.items():

        if value:

            success("API key configured")
            info(f"Source: environment variable ({name})")
            return True

    warn("API key not configured")

    info("Configure using:")
    info("d_Pygen init")
    info("or .env file")
    info("or system environment variable")

    return False



# ============================================================
# OLLAMA CHECK (INSTALLED + RUNNING + CONFIGURED)
# ============================================================

def check_ollama():

    ollama_path = shutil.which("ollama")

    config = load_config()

    configured_model = config.get("ollama_model")

    if ollama_path:

        success("Ollama installed")
        info(ollama_path)

    else:

        warn("Ollama not installed")
        info("Install from: https://ollama.com")
        return False

    # Check if running
    try:

        response = requests.get(
            "http://localhost:11434/api/tags",
            timeout=2
        )

        if response.status_code == 200:

            success("Ollama running")

            models = response.json().get("models", [])

            if models:

                info("Installed models:")

                for m in models:

                    name = m.get("name")

                    if name == configured_model:
                        console.print(f"  • {name} [green](configured)[/green]")
                    else:
                        console.print(f"  • {name}")

            else:

                warn("No Ollama models installed")

            return True

    except:
        pass

    warn("Ollama not running")
    info("Start using:")
    info("ollama serve")
    info("or")
    info("ollama run llama3")

    return False



# ============================================================
# TOOL CHECK
# ============================================================

def check_tool(tool, display):

    path = shutil.which(tool)

    if path:

        try:

            result = subprocess.run(
                [tool, "--version"],
                capture_output=True,
                text=True
            )

            version = result.stdout.split("\n")[0]

            success(display)
            info(f"{version}")
            info(f"{path}")

        except:

            success(display)
            info(path)

        return True

    fail(f"{display} not installed")

    return False


# ============================================================
# TOOLCHAIN CHECK
# ============================================================

def check_toolchains():

    console.print("\n[bold cyan]Toolchains[/bold cyan]\n")

    tools = [

        ("python", "Python"),
        ("pip", "pip"),

        ("node", "Node.js"),
        ("npm", "npm"),
        ("yarn", "Yarn"),
        ("pnpm", "pnpm"),

        ("cargo", "Rust cargo"),
        ("rustc", "Rust compiler"),

        ("go", "Go"),

        ("poetry", "Poetry"),
    ]

    ok = 0

    for tool, name in tools:

        if check_tool(tool, name):
            ok += 1

        console.print()

    return ok, len(tools)


# ============================================================
# PROVIDER CHECK (CONFIG + ENV + AUTO DETECT)
# ============================================================

def check_provider():

    console.print("\n[bold cyan]AI Provider[/bold cyan]\n")

    config = load_config()

    provider = config.get("provider", "auto")

    model = (
        config.get("api_model")
        or config.get("ollama_model")
        or os.getenv("DPYGEN_MODEL")
        or os.getenv("OLLAMA_MODEL")
    )

    fallback = config.get("fallback_provider")

    success(f"Primary provider: {provider}")

    if fallback:
        info(f"Fallback provider: {fallback}")

    if model:
        info(f"Model: {model}")
    else:
        warn("Model not configured")

    # Show source
    if config.get("api_key"):
        info("API source: config.json")

    elif any([
        os.getenv("OPENROUTER_API_KEY"),
        os.getenv("OPENAI_API_KEY"),
        os.getenv("GROQ_API_KEY"),
        os.getenv("TOGETHER_API_KEY")
    ]):
        info("API source: environment variable")

    else:
        warn("No API key configured")

    return True


# ============================================================
# PERMISSIONS
# ============================================================

def check_permissions():

    try:

        test = Path.cwd() / ".doctor_perm"

        test.mkdir(exist_ok=True)
        test.rmdir()

        success("Write permissions OK")

        return True

    except:

        fail("No write permissions")

        return False


# ============================================================
# SUMMARY
# ============================================================

def summary(ok, total):

    console.print()

    if ok == total:

        console.print(
            Panel(
                "[bold green]System fully ready[/bold green]",
                border_style="green"
            )
        )

    else:

        console.print(
            Panel(
                f"[yellow]{total-ok} issues detected[/yellow]",
                border_style="yellow"
            )
        )

    console.print()


# ============================================================
# MAIN
# ============================================================

def run_doctor():

    console.print(
        Panel(
            "[bold cyan]d_Pygen Doctor[/bold cyan]\nSystem diagnostic tool",
            border_style="cyan"
        )
    )

    checks = [

        check_python,
        check_config,
        check_cache,
        check_permissions,
        check_api,
        check_ollama,
        check_provider,
    ]

    ok = 0

    console.print("\n[bold cyan]Core[/bold cyan]\n")

    for c in checks:

        if c():
            ok += 1

        console.print()

    tool_ok, tool_total = check_toolchains()

    total = len(checks) + tool_total

    ok += tool_ok

    summary(ok, total)
