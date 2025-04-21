# ~/taskr/src/taskr/cli/commands/config.py
"""
Configuration command.

This module provides the command for managing Taskr configuration.
"""

import typer
import questionary
import os
import yaml
from typing import Optional, Dict, Any
from rich.table import Table

from taskr.config import getconfig, setconfig, getconfigpath, exportconfig, importconfig, getsectionkeys
from taskr.cli.common import console, getstyle

# Create command app
app = typer.Typer()


@app.callback(invoke_without_command=True)
def configcallback():
    """
    Manage Taskr configuration.

    Use subcommands to get, set, and manage configuration values.
    """
    pass


@app.command("path")
def configpath():
    """Show the path to the configuration file."""
    path = getconfigpath()
    console.print(f"Configuration file: [bold cyan]{path}[/bold cyan]")


@app.command("get")
def configget(
    section: str = typer.Argument(..., help="Configuration section"),
    key: Optional[str] = typer.Argument(None, help="Configuration key")
):
    """Get a configuration value."""
    value = getconfig(section, key)

    if value is None:
        console.print(f"Configuration value not found: [bold cyan]{section}.{key if key else ''}[/bold cyan]")
        return

    if isinstance(value, dict):
        # Print section as table
        table = Table(title=f"Configuration: {section}")
        table.add_column("Key", style="cyan")
        table.add_column("Value")

        for k, v in value.items():
            if isinstance(v, dict):
                v = yaml.dump(v, default_flow_style=False)
            table.add_row(str(k), str(v))

        console.print(table)
    else:
        # Print single value
        console.print(f"{section}.{key}: [bold cyan]{value}[/bold cyan]")


@app.command("set")
def configset(
    section: str = typer.Argument(..., help="Configuration section"),
    key: str = typer.Argument(..., help="Configuration key"),
    value: str = typer.Argument(..., help="Configuration value")
):
    """Set a configuration value."""
    # Convert value type
    if value.lower() == "true":
        parsedvalue = True
    elif value.lower() == "false":
        parsedvalue = False
    elif value.isdigit():
        parsedvalue = int(value)
    elif value.replace(".", "", 1).isdigit():
        parsedvalue = float(value)
    else:
        parsedvalue = value

    # Set value
    setconfig(section, key, parsedvalue)
    console.print(f"Set {section}.{key} = [bold cyan]{parsedvalue}[/bold cyan]")


@app.command("list")
def configlist(
    section: Optional[str] = typer.Argument(None, help="Configuration section")
):
    """List configuration values."""
    if section:
        # List section
        value = getconfig(section)

        if value is None:
            console.print(f"Configuration section not found: [bold cyan]{section}[/bold cyan]")
            return

        table = Table(title=f"Configuration: {section}")
        table.add_column("Key", style="cyan")
        table.add_column("Value")

        if isinstance(value, dict):
            for k, v in value.items():
                if isinstance(v, dict):
                    v = yaml.dump(v, default_flow_style=False)
                table.add_row(str(k), str(v))
        else:
            table.add_row("value", str(value))

        console.print(table)
    else:
        # List all sections
        config = getconfig()

        table = Table(title="Configuration Sections")
        table.add_column("Section", style="cyan")
        table.add_column("Keys")

        for section, value in config.items():
            if isinstance(value, dict):
                keys = ", ".join(value.keys())
            else:
                keys = "value"

            table.add_row(section, keys)

        console.print(table)


@app.command("export")
def configexportcmd(
    output_file: str = typer.Argument(..., help="Output file path")
):
    """Export configuration to a file."""
    success = exportconfig(output_file)

    if success:
        console.print(f"Configuration exported to [bold cyan]{output_file}[/bold cyan]")
    else:
        console.print(f"[bold red]Failed to export configuration.[/bold red]")


@app.command("import")
def configimportcmd(
    input_file: str = typer.Argument(..., help="Input file path")
):
    """Import configuration from a file."""
    success = importconfig(input_file)

    if success:
        console.print(f"Configuration imported from [bold cyan]{input_file}[/bold cyan]")
    else:
        console.print(f"[bold red]Failed to import configuration.[/bold red]")


@app.command("edit")
def configedit():
    """Open configuration file in the default editor."""
    path = getconfigpath()
    editor = os.environ.get("EDITOR", "vi")

    console.print(f"Opening [bold cyan]{path}[/bold cyan] with {editor}...")
    os.system(f"{editor} {path}")


@app.command("interactive")
def configinteractive():
    """Interactively edit configuration."""
    # Set up questionary style
    style = questionary.Style.from_dict(getstyle())

    # Get configuration
    config = getconfig()

    # Prompt for section
    sectionchoices = list(config.keys())
    section = questionary.select(
        "Select configuration section:",
        choices=sectionchoices,
        style=style
    ).ask()

    if not section:
        return

    # Get section data
    sectiondata = getconfig(section)

    if not isinstance(sectiondata, dict):
        # Direct value
        newvalue = questionary.text(
            f"Enter new value for {section}:",
            default=str(sectiondata),
            style=style
        ).ask()

        if newvalue:
            # Convert value type
            if newvalue.lower() == "true":
                parsedvalue = True
            elif newvalue.lower() == "false":
                parsedvalue = False
            elif newvalue.isdigit():
                parsedvalue = int(newvalue)
            elif newvalue.replace(".", "", 1).isdigit():
                parsedvalue = float(newvalue)
            else:
                parsedvalue = newvalue

            # Set value
            setconfig(section, None, parsedvalue)
            console.print(f"Set {section} = [bold cyan]{parsedvalue}[/bold cyan]")

        return

    # Prompt for key
    keychoices = list(sectiondata.keys())
    key = questionary.select(
        f"Select key from {section}:",
        choices=keychoices,
        style=style
    ).ask()

    if not key:
        return

    # Get current value
    currentvalue = sectiondata.get(key)

    # Prompt for new value
    if isinstance(currentvalue, bool):
        newvalue = questionary.confirm(
            f"Enter new value for {section}.{key}:",
            default=currentvalue,
            style=style
        ).ask()
    elif isinstance(currentvalue, (int, float)):
        newvalue = questionary.text(
            f"Enter new value for {section}.{key}:",
            default=str(currentvalue),
            style=style
        ).ask()

        # Convert numeric value
        if newvalue:
            if newvalue.isdigit():
                newvalue = int(newvalue)
            elif newvalue.replace(".", "", 1).isdigit():
                newvalue = float(newvalue)
    elif isinstance(currentvalue, dict):
        # Not supporting nested dicts in interactive mode
        console.print(f"[bold yellow]Cannot edit nested dictionaries interactively.[/bold yellow]")
        console.print(f"Use 'taskr config edit' to edit the configuration file directly.")
        return
    else:
        newvalue = questionary.text(
            f"Enter new value for {section}.{key}:",
            default=str(currentvalue) if currentvalue is not None else "",
            style=style
        ).ask()

    # Set new value
    if newvalue is not None:
        setconfig(section, key, newvalue)
        console.print(f"Set {section}.{key} = [bold cyan]{newvalue}[/bold cyan]")
