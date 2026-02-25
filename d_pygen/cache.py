import json
import hashlib
import time
from pathlib import Path
from d_pygen.logger import logger
from d_pygen.config import load_config



# Cache directory
CACHE_DIR = Path.home() / ".d_pygen" / "cache"
try:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
except Exception as e:
    logger.error(f"Failed to create cache dir: {e}")



def get_default_ttl():
    config = load_config()
    return config.get("cache_ttl", 604800)





def _get_cache_key(prompt: str, provider: str, model: str) -> str:

    key_string = f"{provider}:{model}:{prompt}"

    return hashlib.sha256(
        key_string.encode("utf-8")
    ).hexdigest()


def _is_cache_valid(cache_file: Path, ttl: int) -> bool:

    try:

        modified_time = cache_file.stat().st_mtime

        age = time.time() - modified_time

        return age <= ttl

    except Exception:

        return False


def get_cache(prompt: str, provider: str, model: str, ttl=None):

    if ttl is None:
        ttl = get_default_ttl()

    key = _get_cache_key(prompt, provider, model)

    cache_file = CACHE_DIR / f"{key}.json"

    if not cache_file.exists():

        logger.info("Cache miss")

        return None


    if not _is_cache_valid(cache_file, ttl):

        logger.info("Cache expired")

        try:
            cache_file.unlink()
        except:
            pass

        return None


    try:

        logger.info(
            f"Cache hit | provider={provider} model={model}"
        )

        return json.loads(
            cache_file.read_text(encoding="utf-8")
        )

    except Exception as e:

        logger.error(f"Cache read failed: {e}")

        return None


def save_cache(prompt: str, provider: str, model: str, plan: dict):

    key = _get_cache_key(prompt, provider, model)

    cache_file = CACHE_DIR / f"{key}.json"

    try:

        temp_file = cache_file.with_suffix(".tmp")

        temp_file.write_text(json.dumps(plan, indent=2), encoding="utf-8")

        temp_file.replace(cache_file)

        logger.info(
            f"Saved cache | provider={provider} model={model}"
        )

    except Exception as e:

        logger.error(f"Cache save failed: {e}")




def clear_cache():
    """
    Delete entire cache directory.
    """
    deleted = 0

    for file in CACHE_DIR.glob("*.json"):
        try:
            file.unlink()
            deleted += 1
        except Exception as e:
            logger.error(f"Failed to delete cache file: {e}")

    logger.info(f"Cache cleared ({deleted} files removed)")
    return deleted


def list_cache():
    """
    List all cache entries.
    """
    entries = []

    for file in CACHE_DIR.glob("*.json"):

        try:

            stat = file.stat()

            size = stat.st_size
            modified = stat.st_mtime

            entries.append({
                "file": file.name,
                "size": size,
                "modified": modified
            })

        except Exception as e:
            logger.error(f"Failed reading cache file: {e}")

    return entries


def cache_info():
    """
    Get cache statistics.
    """

    total_files = 0
    total_size = 0

    for file in CACHE_DIR.glob("*.json"):

        try:
            total_files += 1
            total_size += file.stat().st_size

        except:
            pass

    return {
        "location": str(CACHE_DIR),
        "files": total_files,
        "size_bytes": total_size,
        "ttl_days": get_default_ttl() // (24 * 60 * 60)
    }
