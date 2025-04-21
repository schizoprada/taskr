# ~/taskr/src/taskr/cli/commands/info.py
"""
Task info command.

This module provides the command for displaying detailed task information.
"""

import typer
import questionary
from typing import Optional

from taskr.interface import gettask, tasklist
from taskr.cli.common import console, getstyle, printtasktable, printtaskdetails

# Create command app
app = typer.Typer()


@app.callback(invoke_without_command=True)
def infocallback(
        taskid: Optional[int] = typer.Argument(
            None, help="Task ID to display information for"
        ),
        interactive: bool = typer.Option(
            True, "--interactive/--no-interactive", "-i", help="Use interactive mode"
        )
    ):
    """
    Display detailed information about a task.

    By default uses interactive mode. Use --no-interactive to disable.
    """
    if interactive or not taskid:
        infointeractive()
    else:
        _showtaskinfo(taskid)

def infointeractive():
    """Display task information with interactive selection."""
    # Get tasks - use all=True as a fallback if pending filter fails
    tasks = tasklist(includeall=True)

    # Filter to show only pending tasks in the UI by default
    pending_tasks = [task for task in tasks if task.status == "pending"]

    # Display tasks
    if pending_tasks:
        printtasktable(pending_tasks, "Pending Tasks")
    else:
        # If no pending tasks, show all tasks
        printtasktable(tasks, "All Tasks")
        if not tasks:
            console.print("[yellow]No tasks found.[/yellow]")
            return

    # Set up questionary style
    style = questionary.Style.from_dict(getstyle())

    # Create task choices - ask if user wants to see all tasks or just pending
    display_tasks = pending_tasks
    if not pending_tasks and tasks:
        display_all = questionary.confirm(
            "No pending tasks found. Do you want to view information for completed or deleted tasks?",
            default=True,
            style=style
        ).ask()

        if display_all:
            display_tasks = tasks
        else:
            return

    # Create task choices
    choices = [
        questionary.Choice(
            f"{task.id}: {task.description} "
            f"{'[' + task.project + ']' if task.project else ''}"
            f"{' ('+task.status+')' if task.status != 'pending' else ''}",
            task.id
        ) for task in display_tasks
    ]

    # Prompt for task selection
    taskid = questionary.select(
        "Select a task to view:",
        choices=choices,
        style=style
    ).ask()

    if taskid:
        _showtaskinfo(taskid)


def _showtaskinfo(taskid: int):
    """Display detailed information for the specified task."""
    # Get task details
    task = gettask(taskid)

    if not task:
        console.print(f"[bold red]Task {taskid} not found.[/bold red]")
        return

    # Display task details
    printtaskdetails(task)
