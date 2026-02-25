from rich.console import Console

console = Console()


def interactive_create():

    console.print("\n[bold cyan]Interactive Project Creation[/bold cyan]\n")

    # Ask project description
    description = console.input(
        "[green]? What do you want to create? [/green]"
    ).strip()

    if not description:
        console.print("[red]Project description required[/red]")
        return None

    # Ask project name override
    name = console.input(
        "[green]? Project name (optional): [/green]"
    ).strip()

    # Ask template usage
    use_template = console.input(
        "[green]? Use template? (y/n): [/green]"
    ).strip().lower()

    template = None
    variant = None

    if use_template == "y":

        template = console.input(
            "[green]? Template name: [/green]"
        ).strip()

        variant = console.input(
            "[green]? Template variant (default): [/green]"
        ).strip()

        if not variant:
            variant = "default"

    return {
        "description": description,
        "name": name,
        "template": template,
        "variant": variant
    }
