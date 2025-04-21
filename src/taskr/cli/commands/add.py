# ~/taskr/src/taskr/cli/commands/add.py
"""
Add task command.

This module provides the command for adding new tasks.
"""

import typer
import questionary
from typing import Optional, List
from datetime import datetime, timedelta

from taskr.interface import addtask
from taskr.cli.common import console, getstyle, Priority

# Create command app
app = typer.Typer()


@app.callback(invoke_without_command=True)
def addcallback(
    description: Optional[str] = typer.Argument(
        None, help="Task description"
    ),
    project: Optional[str] = typer.Option(
        None, "--project", "-p", help="Project name"
    ),
    priority: Optional[Priority] = typer.Option(
        None, "--priority", "-P", help="Task priority (H, M, L)"
    ),
    tags: Optional[List[str]] = typer.Option(
        None, "--tag", "-t", help="Task tags"
    ),
    due: Optional[str] = typer.Option(
        None, "--due", "-d", help="Due date (YYYY-MM-DD or relative like 'tomorrow')"
    ),
    scheduled: Optional[str] = typer.Option(
        None, "--scheduled", "-s", help="Scheduled date"
    ),
    interactive: bool = typer.Option(
        True, "--interactive/--no-interactive", "-i", help="Use interactive mode"
    )
):
    """
    Add a new task to TaskWarrior.

    By default uses interactive mode. Use --no-interactive to disable.
    """
    if interactive or not description:
        # Interactive mode
        addinteractive()
    else:
        # Command-line mode
        _adddirect(description, project, priority, tags, due, scheduled)


def addinteractive():
    """Add a task with interactive prompts."""
    # Set up questionary style
    style = questionary.Style.from_dict(getstyle())

    # Prompt for task details
    description = questionary.text(
        "Task description:",
        style=style
    ).ask()

    if not description:
        console.print("[bold red]Task creation cancelled.[/bold red]")
        return

    # Prompt for project
    project = questionary.text(
        "Project (optional):",
        style=style
    ).ask()

    # Prompt for priority
    priority = questionary.select(
        "Priority:",
        choices=[
            questionary.Choice("High (H)", "H"),
            questionary.Choice("Medium (M)", "M"),
            questionary.Choice("Low (L)", "L"),
            questionary.Choice("None", "")
        ],
        style=style
    ).ask()

    # Prompt for tags
    tags_input = questionary.text(
        "Tags (space-separated, optional):",
        style=style
    ).ask()

    tags = [tag.strip() for tag in tags_input.split(" ")] if tags_input else None

    # Prompt for due date
    due_choices = [
        questionary.Choice("None", ""),
        questionary.Choice("Today", "today"),
        questionary.Choice("Tomorrow", "tomorrow"),
        questionary.Choice("Next week", "1week"),
        questionary.Choice("Custom date", "custom")
    ]

    due_option = questionary.select(
        "Due date:",
        choices=due_choices,
        style=style
    ).ask()

    due = None
    if due_option == "custom":
        due = questionary.text(
            "Enter due date (YYYY-MM-DD):",
            style=style
        ).ask()
    elif due_option:
        due = due_option

    # Add task
    _adddirect(description, project, priority, tags, due)


def _adddirect(
    description: str,
    project: Optional[str] = None,
    priority: Optional[str] = None,
    tags: Optional[List[str]] = None,
    due: Optional[str] = None,
    scheduled: Optional[str] = None
):
    """Add a task with the given details."""
    # Format dates
    formatted_due = _formatdate(due) if due else None
    formatted_scheduled = _formatdate(scheduled) if scheduled else None

    # Add task
    task = addtask(
        description=description,
        project=project,
        priority=priority,
        tags=tags,
        due=formatted_due,
        scheduled=formatted_scheduled
    )

    if task:
        console.print(f"[bold green]Task {task.id} added successfully.[/bold green]")
    else:
        console.print("[bold red]Failed to add task.[/bold red]")


def _formatdate(date_str: str) -> str:
    """Format date string for TaskWarrior."""
    # Handle relative dates
    if date_str == "today":
        return datetime.now().strftime("%Y-%m-%d")
    elif date_str == "tomorrow":
        return (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    elif date_str.endswith("week"):
        try:
            weeks = int(date_str[0])
            return (datetime.now() + timedelta(weeks=weeks)).strftime("%Y-%m-%d")
        except (ValueError, IndexError):
            return date_str
    elif date_str.endswith("day") or date_str.endswith("days"):
        try:
            days = int(date_str.split()[0])
            return (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
        except (ValueError, IndexError):
            return date_str

    # Return as is for already formatted dates
    return date_str
