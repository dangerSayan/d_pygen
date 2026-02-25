import json
import os
import re
from dotenv import load_dotenv
from rich import print
from d_pygen.logger import logger
from d_pygen.cache import get_cache, save_cache
from d_pygen.config import load_config
from d_pygen.provider_selector import generate_response





# Load environment variables
load_dotenv()


# # Initialize OpenRouter client which is no more needed
# client = OpenAI(
#     api_key=os.getenv("OPENROUTER_API_KEY"),
#     base_url="https://openrouter.ai/api/v1"
# )


def extract_json(text: str):
    """
    Robust JSON extractor that safely finds valid JSON in AI response.
    Handles:
    - markdown ```json blocks
    - extra explanations
    - partial text
    """

    if not text:
        return None

    # Remove markdown code fences if present
    text = re.sub(r"```json", "", text)
    text = re.sub(r"```", "", text)

    # Try direct parse first
    try:
        json.loads(text)
        return text
    except:
        pass

    # Find first valid JSON object by bracket matching
    start = text.find("{")

    if start == -1:
        return None

    bracket_count = 0

    for i in range(start, len(text)):

        if text[i] == "{":
            bracket_count += 1

        elif text[i] == "}":
            bracket_count -= 1

            if bracket_count == 0:
                candidate = text[start:i+1]

                try:
                    json.loads(candidate)
                    return candidate
                except:
                    continue

    return None



def generate_safe_project_name(prompt: str) -> str:
    """
    Generate safe folder name if AI fails to provide one.
    """

    if not prompt:
        return "generated-project"

    name = prompt.lower()

    # Replace spaces with dash
    name = name.replace(" ", "-")

    # Remove invalid characters
    name = re.sub(r'[^a-z0-9\-]', '', name)

    # Limit length
    name = name[:40]

    if not name:
        name = "generated-project"

    return name


def fix_dependency_files(plan: dict):
    """
    Remove invalid dependency files based on project type.
    Ensures only correct dependency manager files exist.
    """

    files = plan.get("files", {})

    has_package_json = "package.json" in files
    has_requirements = "requirements.txt" in files
    has_pyproject = "pyproject.toml" in files
    has_cargo = "Cargo.toml" in files
    has_go = "go.mod" in files

    # =====================================================
    # NODE PROJECT
    # =====================================================

    if has_package_json:

        # Remove Python files
        files.pop("requirements.txt", None)
        files.pop("pyproject.toml", None)
        files.pop("poetry.lock", None)

    # =====================================================
    # PYTHON PROJECT
    # =====================================================

    elif has_requirements or has_pyproject:

        # Remove Node files
        files.pop("package.json", None)
        files.pop("package-lock.json", None)
        files.pop("yarn.lock", None)
        files.pop("pnpm-lock.yaml", None)

    # =====================================================
    # RUST PROJECT
    # =====================================================

    elif has_cargo:

        files.pop("requirements.txt", None)
        files.pop("package.json", None)

    # =====================================================
    # GO PROJECT
    # =====================================================

    elif has_go:

        files.pop("requirements.txt", None)
        files.pop("package.json", None)

    plan["files"] = files

    return plan


def validate_and_fix_plan(plan: dict, prompt: str):
    """
    Validate AI output and auto-fix missing fields.
    """

    if not isinstance(plan, dict):
        print("[red]Invalid AI response format[/red]")
        return None

    # Ensure project_name exists
    if "project_name" not in plan or not plan["project_name"]:

        safe_name = generate_safe_project_name(prompt)

        print(f"[yellow]AI did not provide project_name. Using:[/yellow] {safe_name}")

        plan["project_name"] = safe_name

    # Ensure folders exists
    if "folders" not in plan or not isinstance(plan["folders"], list):

        print("[yellow]AI did not provide folders. Using empty list.[/yellow]")

        plan["folders"] = []

    # Ensure files exists
    if "files" not in plan or not isinstance(plan["files"], dict):

        print("[yellow]AI did not provide files. Using empty dict.[/yellow]")

        plan["files"] = {}

    plan = fix_dependency_files(plan)

    return plan



def generate_project_plan(user_prompt: str, provider_override=None, no_cache=False):
    

    """
    Main function to generate project plan using AI.
    """

    config = load_config()

    # Set provider override
    if provider_override:
        config["provider"] = provider_override

    


    CACHE_ENABLED = config["cache_enabled"]

    logger.info("Generating project plan via AI")
    logger.info(f"Prompt: {user_prompt}")
    logger.info(f"Provider: {config.get('provider')}")
    logger.info(f"Model: {config.get('api_model') or config.get('ollama_model')}")


    # CHECK CACHE FIRST
    cached_plan = None

    provider = config.get("provider", "openrouter")

    if provider == "ollama":
        model = config.get("ollama_model", "default")
    else:
        model = config.get("api_model", "default")


    if CACHE_ENABLED and not no_cache:

        cached_plan = get_cache(
            user_prompt,
            provider,
            model
        )

    else:

        logger.info("Cache disabled (--no-cache)")



    if cached_plan:
        logger.info("Returning cached project plan")
        return cached_plan




    system_prompt = """
        You are a senior software architect.

        Your task is to generate a COMPLETE production-ready project structure.

        You MUST follow ALL rules strictly.

        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        OUTPUT RULES (MANDATORY)
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

        1. Output ONLY valid JSON.
        2. DO NOT include markdown.
        3. DO NOT include explanations.
        4. DO NOT include comments.
        5. DO NOT include text before or after JSON.
        6. DO NOT wrap JSON in ``` blocks.
        7. JSON must start with { and end with }.
        8. JSON must be syntactically valid.

        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        STRUCTURE RULES (MANDATORY)
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

        The JSON MUST contain EXACTLY these keys:

        - project_name (string)
        - folders (array of strings)
        - files (object)

        Example:

        {
        "project_name": "example-project",
        "folders": [
            "app",
            "tests"
        ],
        "files": {
            "README.md": "# Example Project",
            "app/main.py": "print('Hello world')",
            "requirements.txt": "fastapi\\nuvicorn"
        }
        }

        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        FILES RULES (VERY IMPORTANT)
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

        1. Each key in "files" is a file path (string).
        2. Each value in "files" MUST be a STRING.
        3. NEVER return objects inside "files".
        4. NEVER return arrays inside "files".
        5. NEVER return null.
        6. NEVER return nested JSON inside files.

        CORRECT:
        "package.json": "{\\n  \\"name\\": \\"app\\"\\n}"

        WRONG:
        "package.json": {
        "name": "app"
        }

        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        CONTENT RULES
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

        • Generate real production-quality starter code  
        • Use best practices  
        • Include requirements.txt or package.json when appropriate  
        • Include README.md  

        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        FINAL INSTRUCTION
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

        Return ONLY valid JSON.

        NO text.
        NO markdown.
        NO explanation.

        JSON ONLY.
    """



    try:

        content = generate_response(system_prompt, user_prompt, config)

        if not isinstance(content, str):
            logger.error("Provider returned invalid content type")
            return None


        if not content:
            logger.error("Provider failed to generate response")
            return None


        logger.info("========== RAW AI RESPONSE START ==========")
        logger.info(content)
        logger.info("========== RAW AI RESPONSE END ==========")



        json_text = extract_json(content)

        if not json_text:

            print("[red]Failed to extract JSON from AI response[/red]")

            return None

        try:
            plan = json.loads(json_text)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode failed: {e}")
            logger.error(f"Invalid JSON was: {json_text}")
            return None


        # Validate and auto-fix
        plan = validate_and_fix_plan(plan, user_prompt)

        # SAVE TO CACHE
        if CACHE_ENABLED and not no_cache:

            save_cache(
                user_prompt,
                provider,
                model,
                plan
            )




        return plan

    except json.JSONDecodeError:

        print("[red]Invalid JSON returned by AI[/red]")

        return None

    except Exception as e:

        logger.error("AI Engine crashed", exc_info=True)

        error_msg = str(e).lower()

        if "api_key" in error_msg:
            print("[red]Invalid or missing API key. Check OPENROUTER_API_KEY.[/red]")

        elif "timeout" in error_msg:
            print("[yellow]Request timed out. Please try again.[/yellow]")

        elif "network" in error_msg or "connection" in error_msg:
            print("[yellow]Network error. Check your internet connection.[/yellow]")

        else:
            print("[red]AI provider failed. Please try again.[/red]")

        return None


