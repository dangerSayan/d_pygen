import subprocess
import sys
from rich.console import Console

console = Console()


def update_d_pygen():

    console.print("\n[cyan]Checking for updates...[/cyan]\n")

    try:

        console.print("[yellow]Updating d_Pygen via pip...[/yellow]")

        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--upgrade",
                "d_pygen"
            ],
            check=True
        )

        console.print(
            "\n[green]✔ Update check complete.[/green]"
        )


        console.print(
            "[cyan]Restart your terminal to use the new version.[/cyan]"
        )

        return True

    except subprocess.CalledProcessError:

        console.print(
            "[red]Update failed. Try manually:[/red]\n"
            "[white]pip install --upgrade d_pygen[/white]"
        )

        return False

    except Exception as e:

        console.print(f"[red]Update error:[/red] {str(e)}")

        return False
