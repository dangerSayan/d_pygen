import json
import uuid
from datetime import datetime
from pathlib import Path

from d_pygen.config import CONFIG_DIR, load_config
from d_pygen import __version__
from d_pygen.logger import logger


TELEMETRY_FILE = CONFIG_DIR / "telemetry.json"
USER_ID_FILE = CONFIG_DIR / "user_id"
TELEMETRY_CONFIG = CONFIG_DIR / "telemetry_config.json"



# ----------------------------
# Get or create anonymous user id
# ----------------------------

def get_user_id():

    try:

        if USER_ID_FILE.exists():

            return USER_ID_FILE.read_text().strip()

        user_id = str(uuid.uuid4())

        USER_ID_FILE.write_text(user_id)

        return user_id

    except Exception as e:

        logger.error("Telemetry user_id error", exc_info=True)

        return "unknown"


# ----------------------------------------
# Check telemetry status
# ----------------------------------------

def telemetry_status():

    if not TELEMETRY_CONFIG.exists():
        return True  # default enabled

    try:
        config = json.loads(
            TELEMETRY_CONFIG.read_text()
        )
        return config.get("enabled", True)

    except Exception:
        return True




# ----------------------------
# Check if telemetry enabled
# ----------------------------

def telemetry_enabled():

    try:

        config = load_config()

        return config.get("telemetry_enabled", True)

    except Exception:

        return True


# ----------------------------
# Load telemetry data
# ----------------------------

def load_telemetry():

    try:

        if TELEMETRY_FILE.exists():

            return json.loads(
                TELEMETRY_FILE.read_text(encoding="utf-8")
            )

    except Exception:

        pass

    return {
        "user_id": get_user_id(),
        "events": []
    }


# ----------------------------
# Save telemetry data
# ----------------------------

def save_telemetry(data):

    try:

        TELEMETRY_FILE.write_text(
            json.dumps(data, indent=2),
            encoding="utf-8"
        )

    except Exception:

        logger.error("Telemetry save failed", exc_info=True)


# ----------------------------
# Track event
# ----------------------------

def track_event(event_name, metadata=None):

    if not telemetry_status():
        return

    try:

        telemetry = load_telemetry()

        event = {

            "event": event_name,

            "time": datetime.utcnow().isoformat(),

            "version": __version__,

            "user_id": telemetry.get("user_id")

        }

        if metadata:

            event["metadata"] = metadata

        telemetry["events"].append(event)

        save_telemetry(telemetry)

        logger.debug(f"Telemetry tracked: {event_name}")

    except Exception:

        logger.error("Telemetry track failed", exc_info=True)


import json
from pathlib import Path

from d_pygen.config import CONFIG_DIR



# ----------------------------------------
# Enable telemetry
# ----------------------------------------

def enable_telemetry():

    config = {"enabled": True}

    TELEMETRY_CONFIG.write_text(
        json.dumps(config, indent=2),
        encoding="utf-8"
    )

    return True


# ----------------------------------------
# Disable telemetry
# ----------------------------------------

def disable_telemetry():

    config = {"enabled": False}

    TELEMETRY_CONFIG.write_text(
        json.dumps(config, indent=2),
        encoding="utf-8"
    )

    return True



# ----------------------------------------
# Clear telemetry data
# ----------------------------------------

def clear_telemetry():

    if TELEMETRY_FILE.exists():
        TELEMETRY_FILE.unlink()

    return True
