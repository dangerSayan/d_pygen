import requests
from d_pygen.logger import logger


def generate(system_prompt, user_prompt, config):
    """
    Generate response using local Ollama model
    """

    try:

        prompt = f"{system_prompt}\n\n{user_prompt}"

        # FIX: Correct model selection priority
        model = (
            config.get("ollama_model")
            or config.get("model")
            or "llama3:latest"
        )

        logger.info(f"Ollama using model: {model}")

        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False
            },
            timeout=config.get("timeout", 300)
        )

        if response.status_code != 200:

            logger.error(f"Ollama HTTP error: {response.status_code}")
            logger.error(response.text)
            return None

        data = response.json()

        logger.debug(f"Ollama raw response: {data}")

        if "response" in data and data["response"]:

            return data["response"]

        if "message" in data and "content" in data["message"]:

            return data["message"]["content"]

        logger.error(f"Invalid Ollama response format: {data}")
        return None

    except Exception as e:

        logger.error(
            f"Ollama provider error: {e}",
            exc_info=True
        )

        return None