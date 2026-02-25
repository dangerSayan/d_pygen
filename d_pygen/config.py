import os
import json
from pathlib import Path
from d_pygen.logger import logger



# Config directory
CONFIG_DIR = Path.home() / ".d_pygen"
CONFIG_FILE = CONFIG_DIR / "config.json"

PLUGIN_REGISTRY_FILE = CONFIG_DIR / "registry.json"
INSTALLED_PLUGINS_FILE = CONFIG_DIR / "installed.json"



# Default config
DEFAULT_CONFIG = {
    "provider": "auto",

    # PRIMARY provider
    "api_provider": None,
    "api_key": None,
    "api_model": None,

    # FALLBACK provider
    "fallback_provider": None,
    "ollama_model": "llama3:latest",

    # PRIORITY ORDER
    "priority": ["api", "ollama"],

    "base_url": None,
    "max_tokens": 4000,
    "temperature": 0.1,

    "cache_enabled": True,
    "retry_attempts": 3,
    "timeout": 60,

    "cache_ttl": 604800,

    "output_dir": "C:/Dev/projects" if os.name == "nt" else str(Path.home() / "projects"),
}




def _ensure_config_exists():
    """
    Create config file if it doesn't exist.
    """
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    if not CONFIG_FILE.exists():
        CONFIG_FILE.write_text(
            json.dumps(DEFAULT_CONFIG, indent=2),
            encoding="utf-8"
        )
        logger.info("Created default config file")


def load_config():
    """
    Load config from file.
    """
    _ensure_config_exists()

    try:
        config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))

        # Merge with defaults
        merged = {**DEFAULT_CONFIG, **config}

        # Expand output_dir safely
        if "output_dir" in merged and merged["output_dir"]:
            merged["output_dir"] = str(
                Path(merged["output_dir"]).expanduser()
            )

        return merged

    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return DEFAULT_CONFIG


def save_config(new_config: dict):
    """
    Save updated config.
    """
    _ensure_config_exists()

    try:
        CONFIG_FILE.write_text(
            json.dumps(new_config, indent=2),
            encoding="utf-8"
        )
        logger.info("Config saved")

    except Exception as e:
        logger.error(f"Failed to save config: {e}")
