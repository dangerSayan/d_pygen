from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich import box
from rich.tree import Tree
from rich.table import Table
from rich.columns import Columns
from pyfiglet import figlet_format
from datetime import datetime
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.live import Live
import time
from pathlib import Path
from rich.tree import Tree
from rich.panel import Panel
from rich import box

console = Console()


# Banner
def show_banner():

    banner = figlet_format("d_Pygen", font="slant")

    # Strip trailing spaces from each line
    banner = "\n".join(line.rstrip() for line in banner.splitlines())

    text = Text(banner, style="bold bright_cyan")

    panel = Panel(
        Align.center(text),
        box=box.DOUBLE_EDGE,
        border_style="bright_magenta",
        padding=(1, 1),   # reduce horizontal padding
        title="[bright_green]⚡ AI Project Generator CLI ⚡[/bright_green]",
        subtitle="[bright_black]by danger_Sayan[/bright_black]",
        expand=True       # VERY IMPORTANT
    )
    console.print("\n")
    console.print(panel)
    console.print("\n")

# Section header
def show_section(title):

    panel = Panel(
        f"[bold yellow]⚡ {title}[/bold yellow]",
        border_style="yellow",
        box=box.ROUNDED,
        padding=(0, 2)
    )

    console.print()
    console.print(panel)


# Success panel
def show_success(message):

    panel = Panel(
        f"[bold bright_green]✔ SYSTEM ONLINE[/bold bright_green]\n\n[bright_white]{message}[/bright_white]",
        border_style="bright_green",
        box=box.DOUBLE_EDGE,
        padding=(1, 2)
    )

    console.print()
    console.print(panel)



# Error panel
def show_error(message):

    panel = Panel(
        f"[bold red]✗ ERROR[/bold red]\n\n{message}",
        border_style="red",
        box=box.DOUBLE,
        padding=(1, 2)
    )

    console.print()
    console.print(panel)


def show_progress():

    progress = Progress(
        SpinnerColumn(style="bright_cyan"),
        TextColumn("[bright_white]{task.description}"),
        console=console,
        transient=True
    )

    return progress



# Project structure tree
def show_project_structure(project_name, folders, files):

    tree = Tree(f"[bold bright_cyan]📦 {project_name}[/bold bright_cyan]")

    folder_nodes = {}

    for file_path in sorted(files):

        parts = file_path.split("/")

        current = tree
        current_path = ""

        for part in parts[:-1]:

            current_path = f"{current_path}/{part}" if current_path else part

            if current_path not in folder_nodes:

                branch = current.add(
                    f"[bold bright_magenta]📁 {part}[/bold bright_magenta]"
                )

                folder_nodes[current_path] = branch

                current = branch

            else:

                current = folder_nodes[current_path]

        filename = parts[-1]

        current.add(
            f"[bright_green]📄 {filename}[/bright_green]"
        )

    panel = Panel(
        tree,
        title="[bold bright_white]Project Structure[/bold bright_white]",
        border_style="bright_cyan",
        box=box.DOUBLE_EDGE,
        padding=(1, 2)
    )

    console.print()
    console.print(panel)



# Final summary dashboard
def show_summary(project_name, folders, files, start_time):

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    table = Table(show_header=False, box=box.SIMPLE)

    table.add_row("📦 Project Name:", f"[cyan]{project_name}[/cyan]")
    table.add_row("📁 Folders Created:", f"[yellow]{len(folders)}[/yellow]")
    table.add_row("📄 Files Created:", f"[green]{len(files)}[/green]")
    table.add_row("⏱ Setup Time:", f"[magenta]{duration:.2f} seconds[/magenta]")
    table.add_row("🚀 Status:", "[bold green]Ready to use[/bold green]")

    panel = Panel(
        table,
        title="[bold bright_magenta]SYSTEM STATUS[/bold bright_magenta]",
        border_style="bright_magenta",
        box=box.DOUBLE_EDGE,
        padding=(1, 2)
    )


    console.print()
    console.print(panel)


def show_step_success(message):

    console.print(f"[bold bright_green]✔[/bold bright_green] {message}")


def show_final_message(project_name):

    console.print()
    console.print(
        Panel(
            f"[bold bright_green]✔ Project '{project_name}' ready[/bold bright_green]\n\n"
            f"[bright_white]Run:[/bright_white]\n"
            f"[bright_cyan]cd {project_name}[/bright_cyan]\n"
            f"[bright_cyan]python app/main.py[/bright_cyan]",
            border_style="bright_green",
            box=box.DOUBLE_EDGE
        )
    )




def show_project_structure_from_disk(project_path: Path):

    tree = Tree(f"[bold bright_cyan]📦 {project_path.name}[/bold bright_cyan]")

    def add_nodes(parent, path: Path):

        items = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))

        for item in items:

            if item.is_dir():

                branch = parent.add(
                    f"[bold bright_magenta]📁 {item.name}[/bold bright_magenta]"
                )

                add_nodes(branch, item)

            else:

                parent.add(
                    f"[bright_green]📄 {item.name}[/bright_green]"
                )

    add_nodes(tree, project_path)

    panel = Panel(
        tree,
        title="[bold bright_white]Project Structure[/bold bright_white]",
        border_style="bright_cyan",
        box=box.DOUBLE_EDGE,
        padding=(1, 2)
    )

    console.print()
    console.print(panel)
