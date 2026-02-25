import os
import time
from openai import OpenAI
from dotenv import load_dotenv
from d_pygen.logger import logger

load_dotenv()


def generate(system_prompt, user_prompt, config):
    """
    OpenRouter provider with retry + timeout handling
    """

    api_key = config.get("api_key") or os.getenv("OPENROUTER_API_KEY")


    if not api_key:
        logger.error("OPENROUTER_API_KEY not set")
        return None

    client = OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": "https://github.com/dangerSayan/d_pygen",
            "X-Title": "d_Pygen"
        }
    )


    retries = config.get("retry_attempts", 3)
    timeout = config.get("timeout", 60)




    for attempt in range(1, retries + 1):

        try:

            logger.info(f"OpenRouter attempt {attempt}/{retries}")

            model = (
                config.get("api_model")
                or config.get("model")
            )

            if not model:
                logger.error("No OpenRouter model configured")
                return None

            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=config.get("temperature", 0.2),
                max_tokens=config.get("max_tokens", 4000),
                response_format={"type": "json_object"},
                timeout=timeout
            )

            if not response or not response.choices:
                logger.error("Empty response from OpenRouter")
                return None


            logger.info("OpenRouter request successful")

            return response.choices[0].message.content

        except Exception as e:

            logger.warning(f"OpenRouter attempt {attempt} failed: {e}")

            if attempt == retries:
                logger.error("All retry attempts failed", exc_info=True)
                return None

            # exponential backoff
            wait_time = attempt * 2
            logger.info(f"Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
