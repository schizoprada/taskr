# ~/taskr/src/taskr/cli/__init__.py
"""
Taskr CLI module.

This module provides the command-line interface for Taskr.
"""

import typer
import questionary
from typing import Optional, List, Dict

from .commands import (
    add,
    list,
    done,
    delete,
    modify,
    info,
    config,
    backup,
    repeat,
    sync,
)
from taskr.cli.common import getstyle, console

# Create main typer app
app = typer.Typer(
    name="taskr",
    help="Enhanced CLI wrapper for TaskWarrior",
    add_completion=True,
    no_args_is_help=False,  # Changed to False to handle no args ourselves
)

# Register command modules
app.add_typer(add.app, name="add", help="Add a new task")
app.add_typer(list.app, name="list", help="List tasks")
app.add_typer(done.app, name="done", help="Complete a task")
app.add_typer(delete.app, name="delete", help="Delete a task")
app.add_typer(modify.app, name="modify", help="Modify a task")
app.add_typer(info.app, name="info", help="Show task details")
app.add_typer(config.app, name="config", help="Configure Taskr")
app.add_typer(backup.app, name="backup", help="Backup TaskWarrior data")
app.add_typer(repeat.app, name="repeat", help="Repeat a task with specified frequency")
app.add_typer(sync.app, name="sync", help="Sync tasks with external services")


@app.callback()
def maincallback(ctx: typer.Context):
    """
    Taskr - Enhanced CLI wrapper for TaskWarrior.

    Provides interactive task management with a more user-friendly interface.
    """
    # If no command is provided, show interactive command selection
    if ctx.invoked_subcommand is None:
        selectcommandinteractive()


def selectcommandinteractive():
    """
    Display an interactive command selection when running taskr without arguments.
    """
    # Set up questionary style
    style = questionary.Style.from_dict(getstyle())

    # Define command choices with descriptions
    commands = [
        {"name": "add", "description": "Add a new task", "callback": lambda: add.addcallback()},
        {"name": "list", "description": "List tasks", "callback": lambda: list.listcallback()},
        {"name": "done", "description": "Complete a task", "callback": lambda: done.donecallback()},
        {"name": "modify", "description": "Modify a task", "callback": lambda: modify.modifycallback()},
        {"name": "delete", "description": "Delete a task", "callback": lambda: delete.deletecallback()},
        {"name": "info", "description": "Show task details", "callback": lambda: info.infocallback()},
        {"name": "backup", "description": "Backup TaskWarrior data", "callback": lambda: backup.backupcallback(None)},
        {"name": "sync", "description": "Sync tasks with external services", "submenu": [
            {"name": "taskd", "description": "Sync with TaskWarrior Server", "callback": lambda: sync.synctaskd()},
            {"name": "reminders", "description": "Sync with Apple Reminders", "callback": lambda: sync.syncremindersinteractive()},
            {"name": "config", "description": "Configure sync settings", "callback": lambda: sync.syncconfig(None)},
            {"name": "status", "description": "Show sync status", "callback": lambda: sync.syncstatus()},
            {"name": "auto", "description": "Run auto-sync", "callback": lambda: sync.syncauto()},
        ]},
        {"name": "config", "description": "Configure Taskr", "submenu": [
            {"name": "edit", "description": "Edit configuration file", "callback": lambda: config.configedit()},
            {"name": "interactive", "description": "Edit configuration interactively", "callback": lambda: config.configinteractive()},
            {"name": "list", "description": "List configuration values", "callback": lambda: config.configlist(None)},
            {"name": "path", "description": "Show configuration file path", "callback": lambda: config.configpath()},
        ]}
    ]

    # Format choices for questionary
    choices = []
    for cmd in commands:
        if "submenu" in cmd:
            choices.append(questionary.Choice(
                f"{cmd['name']} - {cmd['description']}",
                value={"name": cmd["name"], "submenu": cmd["submenu"]}
            ))
        else:
            choices.append(questionary.Choice(
                f"{cmd['name']} - {cmd['description']}",
                value={"name": cmd["name"], "callback": cmd["callback"]}
            ))

    # Prompt for command selection
    result = questionary.select(
        "Select a command:",
        choices=choices,
        style=style
    ).ask()

    if result:
        if "submenu" in result:
            # Handle submenu
            submenuchoices = [
                questionary.Choice(
                    f"{subcmd['name']} - {subcmd['description']}",
                    value={"name": subcmd["name"], "callback": subcmd["callback"]}
                ) for subcmd in result["submenu"]
            ]

            # Add back option
            submenuchoices.append(questionary.Choice(
                "← Back to main menu",
                value={"name": "back", "callback": None}
            ))

            # Show submenu
            submenuresult = questionary.select(
                f"Select {result['name']} option:",
                choices=submenuchoices,
                style=style
            ).ask()

            if submenuresult and submenuresult["name"] != "back":
                # Execute the callback and explicitly ignore the return value
                submenuresult["callback"]()
                # Don't return anything here - this prevents the return value from displaying
            elif submenuresult and submenuresult["name"] == "back":
                # Go back to main menu
                selectcommandinteractive()
        else:
            # Execute the selected command and explicitly ignore the return value
            result["callback"]()
            # Don't return anything here - this prevents the return value from displaying


if __name__ == "__main__":
    app()
