import argparse
from datetime import datetime
import os

from rich.console import Console

from d_pygen.ai_engine import generate_project_plan
from d_pygen.file_creator import check_dependency_locations, create_project, get_missing_packages
from d_pygen.validator import validate_plan
from d_pygen.logger import logger, set_verbose

from d_pygen.cache import clear_cache, list_cache, cache_info
import time

from d_pygen.doctor import run_doctor

from d_pygen.commands.init import run_init
from d_pygen.core.toolchain import check_project_toolchain
from d_pygen.core.template_engine import load_template
from d_pygen.file_creator import wait_for_dependency_install

from d_pygen.core.plugin_manager import fix_broken_plugins, install_plugin_github

from d_pygen.core.plugin_manager import install_plugin_smart

from d_pygen.core.plugin_manager import (
    get_plugin_info,
    install_plugin,
    uninstall_plugin,
    list_plugins,
    search_plugins,
    update_plugin,
    update_all_plugins,
    check_outdated_plugins,
    upgrade_plugins,
    marketplace_plugins  
)

from d_pygen.core.dependency_manager import scan_dependencies, detect_project_type

from d_pygen.core.dependency_scanner import scan_all
from d_pygen.core.updater import update_d_pygen

from d_pygen.core.telemetry import track_event

from d_pygen.core.telemetry import (
    enable_telemetry,
    disable_telemetry,
    telemetry_status,
    clear_telemetry
)
from d_pygen.core.plugin_validator import validate_github_plugin, validate_local_plugin


from d_pygen.core.template_manager import list_templates

from d_pygen.core.plugin_manager import update_plugin_registry

from d_pygen.core.plugin_manager import clear_plugin_cache

from d_pygen.core.plugin_manager import get_plugin_cache_info


from d_pygen.core.plugin_manager import auto_update_registry_background

from d_pygen.core.interactive import interactive_create


from d_pygen import __version__


from d_pygen.ui import (
    show_banner,
    show_section,
    show_success,
    show_error,
    show_summary,
    show_progress
)

from d_pygen.commands.config import (
    config_show,
    config_set,
    config_reset,
    config_edit,
    config_wizard
)




console = Console()


def step_success(message: str):
    """
    Show professional step success indicator
    """
    console.print(f"[bold bright_green]✔[/bold bright_green] {message}")


def main():

    logger.info("CLI started")
    


    # ---------------------------------------
    # Banner
    # ---------------------------------------

    show_banner()

    # Auto update plugin registry silently
    auto_update_registry_background()
    fix_broken_plugins()



    start_time = datetime.now()

    parser = argparse.ArgumentParser(
        prog="d_Pygen",
        description="""
            AI Project Generator CLI

            Core Commands:
            create                Create new project using AI or template
            init                  Initialize d_Pygen configuration
            doctor                Diagnose system and environment issues
            update                Update d_Pygen to latest version
            version               Show installed version

            Config Commands:
            config show           Show current configuration
            config set KEY VALUE  Set config value
            config edit           Open config file in editor
            config reset          Reset config to default
            config wizard         Interactive config setup

            Plugin Commands:
            plugins install NAME
            plugins uninstall NAME
            plugins list
            plugins search
            plugins info NAME
            plugins marketplace
            plugins update NAME
            plugins update-all
            plugins upgrade
            plugins outdated
            plugins validate NAME
            plugins publish
            plugins registry update
            plugins cache clear
            plugins cache info

            Template Commands:
            templates list

            Cache Commands:
            cache list
            cache clear
            cache info

            Telemetry Commands:
            telemetry status
            telemetry enable
            telemetry disable
            telemetry clear

            Examples:
            d_Pygen create "FastAPI backend"
            d_Pygen create "React app" --provider ollama
            d_Pygen plugins install fastapi
            d_Pygen plugins marketplace
            d_Pygen templates list
        """,
        epilog="""
            Examples:

            d_Pygen create "FastAPI backend"
            d_Pygen create "React app" --provider ollama
            d_Pygen create "CLI tool" --dry-run

            d_Pygen plugins install fastapi
            d_Pygen plugins list
            d_Pygen plugins marketplace

            d_Pygen cache list
            d_Pygen cache clear

            d_Pygen telemetry status

            d_Pygen templates list

            d_Pygen config show
            d_Pygen config set api_provider openrouter
            d_Pygen config wizard


            GitHub:
            https://github.com/dangerSayan/d_pygen
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "command",
        nargs="?",
        help="""
            Command to execute:

            Core:
            create, init, doctor, update, version

            Plugins:
            plugins install/uninstall/list/search/info/update/update-all/
                    upgrade/outdated/validate/publish/marketplace/registry/cache

            Templates:
            templates list

            Cache:
            cache clear/list/info

            Telemetry:
            telemetry status/enable/disable/clear
        """

    )

    parser.add_argument(
        "--variant",
        help="Template variant (e.g., full, minimal)",
        default=None
    )


    parser.add_argument(
        "prompt",
        nargs="?",
        help="Primary argument (project description or plugin action)"
    )

    parser.add_argument(
        "name",
        nargs="?",
        help="Secondary argument (plugin name)"
    )

    parser.add_argument(
        "value",
        nargs="?",
        help="Value for config set command"
    )



    parser.add_argument(
        "--provider",
        help="AI provider (openrouter or ollama)",
        choices=[
            "auto",
            "ollama",
            "openrouter",
            "openai",
            "groq",
            "together",
            "gemini"
        ],

        default=None
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable cache and force fresh generation"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview project structure without creating files"
    )
    parser.add_argument(
        "--output",
        help="Output directory where project will be created",
        default=None
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing project without confirmation"
    )

    parser.add_argument(
        "--name",
        help="Override project name",
        default=None
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    parser.add_argument(
        "--template",
        help="Use local template instead of AI",
        default=None
    )

    parser.add_argument(
        "--install",
        choices=["local", "global", "none"],
        default=None,
        help="Dependency installation mode"
    )


    parser.add_argument(
        "--from",
        dest="source",
        choices=["github", "local"],
        default="github",
        help="Plugin source"
    )



    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return


    # Enable verbose logging if requested
    set_verbose(args.verbose)


    from d_pygen.config import load_config

    config = load_config()

    # Apply config output_dir if CLI flag not provided
    if args.output is None:
        args.output = config.get("output_dir", ".")


    logger.info(f"Command: {args.command}")
    logger.info(f"Prompt: {args.prompt}")

    if args.command == "version":

        console.print(
            f"[bold cyan]d_Pygen version:[/bold cyan] [green]{__version__}[/green]"
        )

        return
    
    if args.command == "help":
        parser.print_help()
        return

    
    # ----------------------------------------
    # TELEMETRY COMMANDS
    # ----------------------------------------

    if args.command == "telemetry":

        if args.prompt == "status":

            enabled = telemetry_status()

            if enabled:
                console.print("[green]Telemetry is ENABLED[/green]")
            else:
                console.print("[yellow]Telemetry is DISABLED[/yellow]")

            return


        elif args.prompt == "enable":

            enable_telemetry()

            console.print("[green]Telemetry enabled[/green]")

            return


        elif args.prompt == "disable":

            disable_telemetry()

            console.print("[yellow]Telemetry disabled[/yellow]")

            return


        elif args.prompt == "clear":

            clear_telemetry()

            console.print("[green]Telemetry data cleared[/green]")

            return


        else:

            console.print(
                "[cyan]Use:[/cyan]\n"
                "  d_Pygen telemetry status\n"
                "  d_Pygen telemetry enable\n"
                "  d_Pygen telemetry disable\n"
                "  d_Pygen telemetry clear"
            )

            return



    if args.command == "plugins":


        if args.prompt == "install":

            plugin_name = args.name

            if not plugin_name:
                show_error("Plugin name required")
                return

            # ALWAYS use smart installer (GitHub default, local fallback)
            success = install_plugin_smart(plugin_name)

            if success:
                track_event("plugin_installed", {"plugin": plugin_name})

            return

        
        elif args.prompt == "marketplace":

            marketplace_plugins()

            track_event("plugins_marketplace_viewed")

            return

        

        elif args.prompt == "registry":

            if args.name == "update":

                success = update_plugin_registry()

                if success:
                    track_event("plugin_registry_updated")

                return

            else:

                console.print(
                    "[cyan]Use:[/cyan]\n"
                    "  d_Pygen plugins registry update"
                )

                return
        
        elif args.prompt == "validate":

            plugin_name = args.name

            if not plugin_name:
                console.print("[red]Plugin name required[/red]")
                return


            info = get_plugin_info(plugin_name)

            if not info:
                console.print("[red]Plugin not found in registry[/red]")
                return

            validate_github_plugin(
                info["repo"],
                info.get("branch", "main")
            )

            return
        
        elif args.prompt == "cache":

            if args.name == "clear":

                clear_plugin_cache()

            elif args.name == "info":

                info = get_plugin_cache_info()

                size_mb = info["size_bytes"] / (1024 * 1024)

                console.print("\n[bold cyan]Plugin Cache Information[/bold cyan]\n")

                console.print(f"Location: {info['location']}")
                console.print(f"Plugins cached: {info['plugins']}")
                console.print(f"Total size: {size_mb:.2f} MB\n")

                if info["breakdown"]:

                    console.print("[bold]Breakdown:[/bold]\n")

                    for name, size in info["breakdown"].items():

                        size_mb = size / (1024 * 1024)

                        console.print(f"  {name:<15} {size_mb:.2f} MB")

                else:

                    console.print("[dim]No cached plugins[/dim]")

            else:

                console.print(
                    "Use:\n"
                    "d_Pygen plugins cache clear\n"
                    "d_Pygen plugins cache info"
                )

            return


        elif args.prompt == "uninstall":

            plugin_name = args.name

            if not plugin_name:
                show_error("Plugin name required")
                return

            success = uninstall_plugin(plugin_name)

            if success:
                track_event("plugin_uninstalled", {"plugin": plugin_name})

            return


        elif args.prompt == "list":

            plugins = list_plugins()

            if not plugins:
                console.print("[yellow]No plugins installed[/yellow]")
            else:
                console.print("\nInstalled plugins:\n")
                for p in plugins:
                    console.print(f"[green]✔[/green] {p}")

            return


        elif args.prompt == "search":

            plugins = search_plugins()

            if not plugins:
                console.print("[red]No plugins found[/red]")
                return

            console.print("\nAvailable plugins:\n")

            for plugin in plugins:

                console.print(
                    f"[bold green]{plugin['name']}[/bold green]\n"
                    f"   {plugin['description']}\n"
                )

            return


        elif args.prompt == "info":

            plugin_name = args.name

            if not plugin_name:
                show_error("Plugin name required")
                return

            info = get_plugin_info(plugin_name)

            if not info:
                console.print("[red]Plugin not found[/red]")
                return

            console.print(f"\nPlugin: {plugin_name}")
            console.print(f"Description: {info.get('description')}")
            console.print(f"Repo: {info.get('repo')}")

            return

        elif args.prompt == "upgrade":

            success = upgrade_plugins()

            if success:
                track_event("plugins_upgraded", {})


            return


        elif args.prompt == "update":     

            plugin_name = args.name

            if not plugin_name:
                show_error("Plugin name required")
                return

            success = update_plugin(plugin_name)

            if success:
                track_event("plugin_updated", {"plugin": plugin_name})

            return


        elif args.prompt == "update-all":   

            update_all_plugins()

            track_event("plugins_updated_all")

            return
        
        elif args.prompt == "outdated":

            outdated = check_outdated_plugins()

            if not outdated:
                console.print("[green]All plugins are up to date[/green]")
                return

            console.print("[yellow]Updates available:\n[/yellow]")

            for plugin in outdated:

                console.print(
                    f"[bold]{plugin['name']}[/bold]\n"
                    f"   installed: {plugin['installed']}\n"
                    f"   latest:    {plugin['latest']}\n"
                )

            return
        
        elif args.prompt == "publish":

            from d_pygen.core.plugin_publisher import publish_plugin

            token = os.getenv("DPYGEN_GITHUB_TOKEN")

            publish_plugin(token)

            return




        else:

            show_error(
                "Use: install, uninstall, list, search, marketplace, info, update, update-all, outdated, upgrade"
            )

            return
        



    # ============================================
    # CONFIG COMMAND
    # ============================================

    if args.command == "config":

        if args.prompt == "show":

            config_show()
            return
        
        elif args.prompt == "wizard":

            config_wizard()
            return


        elif args.prompt == "set":

            key = args.name
            value = args.value

            if not key or value is None:

                console.print(
                    "[yellow]Usage:[/yellow]\n"
                    "  d_Pygen config set provider ollama\n"
                    "  d_Pygen config set model llama3\n"
                    "  d_Pygen config set api_key sk-xxxxx"
                )
                return

            config_set(key, value)
            return


        elif args.prompt == "reset":

            config_reset()
            return

        elif args.prompt == "edit":

            config_edit()
            return

        else:

            console.print(
                "[cyan]Config commands:[/cyan]\n"
                "  d_Pygen config show\n"
                "  d_Pygen config set provider ollama\n"
                "  d_Pygen config set model llama3\n"
                "  d_Pygen config edit\n"
                "  d_Pygen config reset"
            )

            return




    if args.command == "init":

        run_init()
        track_event("init_run")

        return


    if args.command == "doctor":

        run_doctor()

        return

    elif args.command == "update":

        update_d_pygen()

        return
    
    elif args.command == "templates":

        if args.prompt == "list":

            templates = list_templates()

            if not templates:

                console.print("[yellow]No templates installed[/yellow]")
                return

            console.print("\nInstalled templates:\n")

            for t in templates:

                console.print(f"[green]{t}[/green]")

            return
        
        else:
            show_error("Use: templates list")
            return



    if args.command == "cache":

        if args.prompt == "clear":

            deleted = clear_cache()

            console.print(
                f"[bold green]✔ Cache cleared ({deleted} files removed)[/bold green]"
            )
            return


        elif args.prompt == "list":

            entries = list_cache()

            if not entries:
                console.print("[yellow]No cache entries found[/yellow]")
                return

            console.print("\n[bold cyan]Cached project plans:[/bold cyan]\n")

            for i, entry in enumerate(entries, 1):

                age_seconds = time.time() - entry["modified"]

                if age_seconds < 60:
                    age = f"{int(age_seconds)} sec ago"
                elif age_seconds < 3600:
                    age = f"{int(age_seconds/60)} min ago"
                elif age_seconds < 86400:
                    age = f"{int(age_seconds/3600)} hours ago"
                else:
                    age = f"{int(age_seconds/86400)} days ago"

                console.print(
                    f"[green]{i}.[/green] "
                    f"{entry['file']} "
                    f"[dim]({age})[/dim]"
                )

            return


        elif args.prompt == "info":

            info = cache_info()

            size_mb = info["size_bytes"] / (1024 * 1024)

            console.print("\n[bold cyan]Cache Information[/bold cyan]\n")

            console.print(f"Location: {info['location']}")
            console.print(f"Files: {info['files']}")
            console.print(f"Size: {size_mb:.2f} MB")
            console.print(f"TTL: {info['ttl_days']} days")

            return


        else:
            show_error("Invalid cache command. Use: clear, list, or info")
            return



    elif args.command == "create":

        if not args.prompt:

            result = interactive_create()

            if not result:
                return

            # project description
            args.prompt = result["description"]

            # project name override
            if result["name"]:
                args.name = result["name"]

            # template usage
            if result["template"]:
                args.template = result["variant"]

                # store template name separately
                args.template_name = result["template"]
            else:
                args.template_name = None


    else:
        show_error(
            f"Unknown command: '{args.command}'\n\n"
            "Run 'd_Pygen help' to see available commands."
        )

        return



    # ---------------------------------------
    # STEP 1: Generate project plan
    # ---------------------------------------

    show_section("Generating project plan")

    progress = show_progress()

    with progress:

        task = progress.add_task(
            "[bright_cyan]Contacting AI engine...\n",
            total=None   # spinner mode (professional)
        )

        # If template specified, use template engine
        if args.template:

            template_name = args.template
            variant = args.variant or "default"

            try:

                plan = load_template(template_name, variant)

            except Exception as e:

                show_error(str(e))
                return

        else:

            
            config = load_config()

            # If no provider configured, skip AI immediately
            if not config.get("api_provider") and not config.get("fallback_provider"):

                show_error(
                    "No AI provider configured.\n\n"
                    "Run 'd_Pygen init' to configure one.\n"
                    "Or use: d_Pygen create --template <template_name>"
                )

                return

            plan = generate_project_plan(
                args.prompt,
                provider_override=args.provider,
                no_cache=args.no_cache
            )

            # FALLBACK SYSTEM
            if not plan:

                console.print(
                    "[yellow]AI failed. Trying template fallback...[/yellow]"
                )

                try:

                    plan = load_template(args.prompt, "default")

                    console.print(
                        "[green]Template fallback successful[/green]"
                    )

                except Exception:

                    

                    config = load_config()

                    # Detect if no provider configured
                    if not config.get("api_provider") and not config.get("fallback_provider"):

                        show_error(
                            "No AI provider configured.\n\n"
                            "Run 'd_Pygen init' to configure one.\n"
                            "Or use: d_Pygen create --template <template_name>"
                        )

                    else:

                        show_error(
                            "All configured AI providers failed.\n\n"
                            "Check your API key, internet connection, or Ollama status."
                        )

                    return



        progress.stop_task(task)

    console.print()

    if not plan:

        logger.error("AI failed to generate project plan")
        show_error("AI failed to generate project plan")
        return

    if not validate_plan(plan):

        show_error("Project plan validation failed")
        return
    
    # Override project name if user specified --name
    if args.name:

        original_name = plan.get("project_name")

        plan["project_name"] = args.name

        logger.info(
            f"Project name overridden: {original_name} → {args.name}"
        )


    step_success("Project plan generated")

    # ---------------------------------------
    # Preview project structure ONLY in dry-run mode
    # ---------------------------------------

    from d_pygen.ui import show_project_structure

    if args.dry_run:

        show_project_structure(
            plan["project_name"],
            plan.get("folders", []),
            plan.get("files", {}).keys()
        )

        console.print()

        confirm = console.input(
            "[bold yellow]Create this project? (y/n): [/bold yellow]"
        ).strip().lower()

        if confirm != "y":

            console.print(
                "[yellow]Project creation cancelled.[/yellow]"
            )

            logger.info("User cancelled project creation after dry-run")

            return

        console.print(
            "[green]Proceeding with project creation...[/green]\n"
        )




    logger.info(f"Project created successfully: {plan['project_name']}")


    # ---------------------------------------
    # STEP 2: Create project structure
    # ---------------------------------------

    show_section("Creating project structure")

    progress = show_progress()

    with progress:

        task = progress.add_task(
            "[bright_magenta]Preparing project...",
            total=None
        )

        # stop spinner BEFORE file creation
        progress.stop_task(task)

    console.print()

    # now safe to call create_project (input works correctly)
    project_path, install_mode = create_project(
        plan,
        output_dir=args.output,
        dry_run=False,
        force=args.force,
        install_mode=args.install
    )

    

    





    if not project_path:
        show_error("Project creation cancelled")
        return

    step_success("Project structure created")

    # TELEMETRY
    track_event(
        "project_created",
        {"project": plan["project_name"]}
    )



    # ---------------------------------------
    # STEP 3: Summary dashboard
    # ---------------------------------------

    show_summary(
        plan["project_name"],
        plan.get("folders", []),
        plan.get("files", {}),
        start_time
    )

    # Wait until dependency installation completes FIRST
    status = wait_for_dependency_install()

    project_type = detect_project_type(project_path)
    missing = []

    # Always check toolchain readiness
    toolchain_results = check_project_toolchain(project_type, show=False)

    for tool in toolchain_results:
        if not tool["found"]:
            missing.append(tool["name"])



    

    # ---------------------------------------
    # Dependency Status Handling (Universal)
    # ---------------------------------------

    if status == "installed":

        console.print(
            "[bold green]✔ Dependencies installed successfully[/bold green]"
        )


    elif status == "skipped":

        console.print(
            "[bold yellow]⚠ You skipped installing dependencies[/bold yellow]"
        )

        console.print(
            f"[bold cyan]Detected project type:[/bold cyan] {project_type}\n"
        )

        deps = scan_all(project_path)


        if not deps:

            console.print(
                "[yellow]No dependency information found[/yellow]"
            )

        else:

            console.print("[bold cyan]Environment check:[/bold cyan]\n")

            system_items = []
            project_items = []
            dependency_items = []

            # Categorize properly
            for pkg in deps:

                pkg_type = pkg.get("type", "dependency")

                if pkg_type == "project":
                    project_items.append(pkg)

                elif pkg_type == "system":
                    system_items.append(pkg)

                elif pkg_type == "dependency":
                    dependency_items.append(pkg)

                else:
                    dependency_items.append(pkg)


            runtime_missing = False

            # =====================================================
            # PROJECT SECTION (ALWAYS SHOW)
            # =====================================================

            console.print("[bold]Project:[/bold]\n")

            if project_items:

                for pkg in project_items:

                    locations = (
                        ", ".join(pkg.get("locations", []))
                        or pkg.get("path")
                        or "unknown"
                    )


                    if pkg.get("found", False):

                        console.print(
                            f"  [green]✔ {pkg['name']} detected[/green] ({locations})"
                        )

                    else:

                        console.print(
                            f"  [red]✘ {pkg['name']} not detected[/red]"
                        )

                        missing.append(pkg["name"])

            else:

                console.print("  [yellow]⚠ No project metadata found[/yellow]")

            console.print()


            # =====================================================
            # RUNTIME SECTION (ALWAYS SHOW)
            # =====================================================

            console.print("[bold]Runtime:[/bold]\n")

            if system_items:

                for pkg in system_items:

                    locations = (
                        ", ".join(pkg.get("locations", []))
                        or pkg.get("path")
                        or "unknown"
                    )


                    if pkg.get("found", False):

                        console.print(
                            f"  [green]✔ {pkg['name']} installed[/green] ({locations})"
                        )

                    else:

                        console.print(
                            f"  [red]✘ {pkg['name']} not installed[/red]"
                        )

                        runtime_missing = True
                        missing.append(pkg["name"])

            else:

                console.print("  [yellow]⚠ No runtime detected[/yellow]")

            console.print()


            # =====================================================
            # DEPENDENCIES SECTION (ALWAYS SHOW)
            # =====================================================

            console.print("[bold]Dependencies:[/bold]\n")

            if dependency_items:

                if runtime_missing:

                    console.print(
                        "  [yellow]⚠ Cannot verify dependencies (runtime missing)[/yellow]"
                    )

                else:

                    for pkg in dependency_items:

                        locations = ", ".join(pkg.get("locations", [])) or "not installed"

                        if pkg.get("found", False):

                            console.print(
                                f"  [green]✔ {pkg['name']}[/green] ({locations})"
                            )

                        else:

                            console.print(
                                f"  [red]✘ {pkg['name']} missing[/red]"
                            )

                            missing.append(pkg["name"])

            else:

                console.print("  [yellow]⚠ No dependencies found[/yellow]")

            console.print()


            # =====================================================
            # FINAL STATUS
            # =====================================================

            if missing:

                console.print(
                    "[bold red]✘ Environment broken[/bold red] "
                    "[dim](missing required tools or dependencies)[/dim]"
                )

            else:

                console.print(
                    "[bold green]✔ Environment healthy[/bold green] "
                    "[dim](all required tools and dependencies available)[/dim]"
                )

            console.print()


            



    elif status == "installing":

        console.print(
            "[yellow]Dependencies still installing in background...[/yellow]"
        )

    elif status == "failed":

        console.print(
            "[bold red]✘ Dependency installation failed[/bold red]"
        )

        console.print(
            "[yellow]Some or all dependencies may not be installed.[/yellow]"
        )

        missing.append("dependencies")

    else:

        deps = scan_all(project_path)

        if deps and all(pkg.get("found") for pkg in deps):

            console.print(
                "[bold green]✔ All dependencies already available[/bold green]"
            )

        else:

            console.print(
                "[bold yellow]⚠ Dependencies not fully installed[/bold yellow]"
            )

            missing.append("dependencies")






    # ---------------------------------------
    # STEP 4: Final success panel
    # ---------------------------------------

    show_success(
        f"Project '{plan['project_name']}' created successfully."
    )

    if len(missing) > 0:
        console.print("[bold red]System ready: NO[/bold red]")
    else:
        console.print("[bold green]System ready: YES[/bold green]")


    console.print()


    # ---------------------------------------
    # DEPENDENCY WARNING IF NOT INSTALLED
    # ---------------------------------------
    project_type = detect_project_type(project_path)

    # Show toolchain status (visual only)
    check_project_toolchain(project_type, show=True)

    if missing:
        console.print(
            "\n[black on yellow bold] Install the required tools above and run again. [/black on yellow bold]\n"
        )



    


    # ---------------------------------------
    # NEXT STEPS SECTION (UNIVERSAL)
    # ---------------------------------------

    console.print("\n[bold cyan]Next steps:[/bold cyan]\n")

    # Navigate
    console.print("[bold]Go to your project:[/bold]")
    console.print(f'  cd "{project_path}"\n')

    # VS Code
    console.print("[bold]Open in VS Code:[/bold]")
    console.print("  code .\n")

    


    # =====================================================
    # PYTHON (pip)
    # =====================================================

    if project_type == "python-pip":

        if install_mode == "local":

            console.print("[bold]Activate virtual environment:[/bold]\n")

            if os.name == "nt":
                console.print("  .venv\\Scripts\\Activate.ps1    (PowerShell)")
                console.print("  .venv\\Scripts\\activate.bat    (CMD)")
            else:
                console.print("  source .venv/bin/activate")

            console.print()

        elif install_mode == "none":

            console.print("[bold yellow]Install dependencies:[/bold yellow]\n")

            console.print("  python -m venv .venv")

            if os.name == "nt":
                console.print("  .venv\\Scripts\\Activate.ps1")
            else:
                console.print("  source .venv/bin/activate")

            console.print("  pip install -r requirements.txt\n")

        console.print("[bold]Run the project:[/bold]\n")
        console.print("  uvicorn app.main:app --reload\n")


    # =====================================================
    # PYTHON (Poetry)
    # =====================================================

    elif project_type == "python-poetry":

        if install_mode == "none":
            console.print("[bold yellow]Install dependencies:[/bold yellow]\n")
            console.print("  poetry install\n")

        console.print("[bold]Run the project:[/bold]\n")
        console.print("  poetry run python main.py\n")


    # =====================================================
    # NODE (npm)
    # =====================================================

    elif project_type == "node-npm":

        if install_mode == "none":
            console.print("[bold yellow]Install dependencies:[/bold yellow]\n")
            console.print("  npm install\n")

        console.print("[bold]Run the project:[/bold]\n")
        console.print("  npm run dev")
        console.print("  # or")
        console.print("  npm start\n")


    # =====================================================
    # NODE (yarn)
    # =====================================================

    elif project_type == "node-yarn":

        if install_mode == "none":
            console.print("[bold yellow]Install dependencies:[/bold yellow]\n")
            console.print("  yarn install\n")

        console.print("[bold]Run the project:[/bold]\n")
        console.print("  yarn dev")
        console.print("  # or")
        console.print("  yarn start\n")


    # =====================================================
    # NODE (pnpm)
    # =====================================================

    elif project_type == "node-pnpm":

        if install_mode == "none":
            console.print("[bold yellow]Install dependencies:[/bold yellow]\n")
            console.print("  pnpm install\n")

        console.print("[bold]Run the project:[/bold]\n")
        console.print("  pnpm dev")
        console.print("  # or")
        console.print("  pnpm start\n")


    # =====================================================
    # RUST
    # =====================================================

    elif project_type == "rust":

        console.print("[bold]Build project:[/bold]\n")
        console.print("  cargo build\n")

        console.print("[bold]Run the project:[/bold]\n")
        console.print("  cargo run\n")


    # =====================================================
    # GO
    # =====================================================

    elif project_type == "go":

        if install_mode == "none":
            console.print("[bold yellow]Download dependencies:[/bold yellow]\n")
            console.print("  go mod tidy\n")

        console.print("[bold]Run the project:[/bold]\n")
        console.print("  go run .\n")


    # =====================================================
    # FALLBACK
    # =====================================================

    else:

        console.print("[yellow]Unknown project type. Check README.md for instructions.[/yellow]\n")


    # =====================================================
    # UNIVERSAL
    # =====================================================

    console.print("[bold]Explore project files:[/bold]")

    console.print("  explorer .     (Windows)")
    console.print("  open .         (macOS)")
    console.print("  xdg-open .     (Linux)\n")

    console.print("[dim]Project location:[/dim]")
    console.print(f"[green]{project_path}[/green]\n")


    




if __name__ == "__main__":
    main()
