import os
import requests

from d_pygen.providers import openai_compatible_provider

from d_pygen.logger import logger

from rich.console import Console

console = Console()



# Detect if Ollama is running locally
def is_ollama_running():
    try:
        response = requests.get(
            "http://localhost:11434/api/tags",
            timeout=2
        )
        return response.status_code == 200
    except:
        return False


def generate_response(system_prompt, user_prompt, config, provider_override=None):

    # -----------------------------------------
    # STEP 1: Determine provider priority
    # -----------------------------------------

    if provider_override:

        logger.info(f"CLI override detected: {provider_override}")

        if provider_override == "ollama":

            priority = ["ollama", "api"]

        elif provider_override in ["openrouter", "openai", "groq", "together"]:

            priority = ["api", "ollama"]

        else:

            priority = config.get("priority", ["api", "ollama"])

    else:

        priority = config.get("priority", ["api", "ollama"])


    # -----------------------------------------
    # STEP 2: Try providers in priority order
    # -----------------------------------------

    for provider_type in priority:

        # ==========================
        # TRY API PROVIDER
        # ==========================

        if provider_type == "api":

            provider = config.get("api_provider")

            if not provider:
                logger.warning("No API provider configured")
                continue

            logger.info(f"Trying API provider: {provider}")

            try:

                result = openai_compatible_provider.generate(
                    system_prompt,
                    user_prompt,
                    config
                )

                if result:

                    logger.info("API provider success")

                    return result

                else:

                    logger.warning("API provider returned empty result")

            except Exception as e:

                logger.warning(f"API provider failed: {e}")


        # ==========================
        # TRY OLLAMA PROVIDER
        # ==========================

        elif provider_type == "ollama":

            if not is_ollama_running():

                logger.warning("Ollama not running")

                continue

            logger.info("Trying Ollama provider")

            try:

                from d_pygen.providers import ollama_provider

                ollama_config = config.copy()

                result = ollama_provider.generate(
                    system_prompt,
                    user_prompt,
                    ollama_config
                )

                if result:

                    logger.info("Ollama success")

                    return result

                else:

                    logger.warning("Ollama returned empty result")

            except Exception as e:

                logger.warning(f"Ollama failed: {e}")


    # -----------------------------------------
    # STEP 3: All failed
    # -----------------------------------------

    console.print("[red]All AI providers failed[/red]")

    return None
