import logging
from pathlib import Path

# Create hidden directory in user's home
LOG_DIR = Path.home() / ".d_pygen"
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "d_pygen.log"


def setup_logger():
    """
    Configure professional logging system.
    """

    logger = logging.getLogger("d_pygen")

    logger.propagate = False


    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    # File handler
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.INFO)

    # Console handler (mark with attribute)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)

    # mark this as console handler
    console_handler._is_console = True

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )

    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger



logger = setup_logger()


# ADD THIS FUNCTION
def set_verbose(enabled: bool):
    """
    Enable verbose logging in console only.
    """

    if not enabled:
        return

    for handler in logger.handlers:
        if getattr(handler, "_is_console", False):
            handler.setLevel(logging.INFO)

    logger.info("Verbose mode enabled")

