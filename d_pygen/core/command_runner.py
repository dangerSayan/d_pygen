import subprocess
import shutil
import os


def run_command(command, cwd=None, silent=False):
    """
    Universal cross-platform command runner

    Works on:
    Windows (.cmd, .bat, .exe)
    Linux
    macOS
    WSL
    Docker
    CI/CD

    command: list[str]
    cwd: Path or str
    silent: suppress output
    """

    tool = command[0]

    tool_path = shutil.which(tool)

    if not tool_path:
        raise RuntimeError(f"{tool} not found in PATH")

    # Windows fix (.cmd, .bat resolution)
    if os.name == "nt":

        cmd = tool_path + ".cmd"
        bat = tool_path + ".bat"

        if os.path.exists(cmd):
            tool_path = cmd
        elif os.path.exists(bat):
            tool_path = bat

    full_command = [tool_path] + command[1:]

    subprocess.run(
        full_command,
        cwd=str(cwd) if cwd else None,
        check=True,
        stdout=subprocess.DEVNULL if silent else None,
        stderr=subprocess.DEVNULL if silent else None
    )

    return True
