from openai import OpenAI
from d_pygen.logger import logger


PROVIDER_URLS = {

    "openrouter": "https://openrouter.ai/api/v1",

    "openai": "https://api.openai.com/v1",

    "groq": "https://api.groq.com/openai/v1",

    "together": "https://api.together.xyz/v1"
}


def generate(system_prompt, user_prompt, config):

    provider = config.get("api_provider")


    base_url = config.get("base_url") or PROVIDER_URLS.get(provider)

    api_key = config.get("api_key")

    if not base_url:
        logger.error("No base_url configured")
        return None

    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )

    try:

        model = (
            config.get("api_model")
            or config.get("model")
        )

        if not model:
            logger.error("No API model configured")
            return None

        response = client.chat.completions.create(

            model=model,

            messages=[

                {"role": "system", "content": system_prompt},

                {"role": "user", "content": user_prompt}

            ],

            temperature=config.get("temperature", 0.2),

            max_tokens=config.get("max_tokens", 4000),

            timeout=config.get("timeout", 300)
        )

        return response.choices[0].message.content

    except Exception as e:

        logger.error(f"{provider} provider failed: {e}")

        return None
