# ~/taskr/src/taskr/cli/commands/done.py
"""
Complete task command.

This module provides the command for marking tasks as completed.
"""

import typer
import questionary
from typing import Optional, List

from taskr.interface import completetask, tasklist, gettask
from taskr.cli.common import console, getstyle, printtasktable, confirmaction

# Create command app
app = typer.Typer()


@app.callback(invoke_without_command=True)
def donecallback(
    taskid: Optional[int] = typer.Argument(
        None, help="Task ID to mark as completed"
    ),
    interactive: bool = typer.Option(
        True, "--interactive/--no-interactive", "-i", help="Use interactive mode"
    )
):
    """
    Mark a task as completed.

    By default uses interactive mode. Use --no-interactive to disable.
    """
    if interactive or not taskid:
        doneinteractive()
    else:
        _completetask(taskid)


def doneinteractive():
    """Mark a task as completed with interactive selection."""
    # Get tasks - use all=True as a fallback if pending filter fails
    tasks = tasklist(includeall=True)

    # Filter to show only pending tasks in the UI
    pending_tasks = [task for task in tasks if task.status == "pending"]

    # Display tasks
    if pending_tasks:
        printtasktable(pending_tasks, "Pending Tasks")
    else:
        console.print("[yellow]No pending tasks found. Nothing to complete.[/yellow]")
        return

    if not pending_tasks:
        return

    # Set up questionary style
    style = questionary.Style.from_dict(getstyle())

    # Create task choices
    choices = [
        questionary.Choice(
            f"{task.id}: {task.description} "
            f"{'[' + task.project + ']' if task.project else ''}",
            task.id
        ) for task in pending_tasks
    ]

    # Prompt for task selection
    taskid = questionary.select(
        "Select a task to complete:",
        choices=choices,
        style=style
    ).ask()

    if taskid:
        _completetask(taskid)


def _completetask(taskid: int):
    """Mark the specified task as completed."""
    # Get task details
    task = gettask(taskid)

    if not task:
        console.print(f"[bold red]Task {taskid} not found.[/bold red]")
        return

    # Confirm completion
    confirmed = confirmaction(f"Complete task {taskid}: {task.description}?")

    if not confirmed:
        console.print("Task completion cancelled.")
        return

    # Complete task
    success = completetask(taskid)

    if success:
        console.print(f"[bold green]Task {taskid} completed successfully.[/bold green]")
    else:
        console.print(f"[bold red]Failed to complete task {taskid}.[/bold red]")
