from rich import print
from d_pygen.logger import logger

def validate_plan(plan):

    if not plan:
        logger.error("Invalid plan received")
        print("[red]Invalid plan[/red]")
        return False


    required_keys = ["project_name", "folders", "files"]

    for key in required_keys:

        if key not in plan:
            logger.error(f"Missing key: {key}")
            print(f"[red]Missing key: {key}[/red]")
            return False


    if not isinstance(plan["folders"], list):
        print("[red]folders must be list[/red]")
        return False

    if not isinstance(plan["files"], dict):
        print("[red]files must be dict[/red]")
        return False

    return True
