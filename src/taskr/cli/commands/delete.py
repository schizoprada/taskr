# ~/taskr/src/taskr/cli/commands/delete.py
"""
Delete task command.

This module provides the command for deleting tasks.
"""

import typer
import questionary
import re
from typing import Optional, List, Union

from taskr.interface import deletetask, tasklist, gettask
from taskr.cli.common import console, getstyle, printtasktable, confirmaction

# Create command app
app = typer.Typer()


@app.callback(invoke_without_command=True)
def deletecallback(
    taskid: Optional[str] = typer.Argument(
        None, help="Task ID or range (e.g., 2:5, 2:, :7) to delete"
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Force deletion without confirmation"
    ),
    interactive: bool = typer.Option(
        True, "--interactive/--no-interactive", "-i", help="Use interactive mode"
    )
):
    """
    Delete a task or range of tasks.

    Examples:
        taskr delete 2     # delete task 2
        taskr delete 2:5   # delete tasks 2 through 5
        taskr delete 2:    # delete tasks 2 and onwards
        taskr delete :7    # delete tasks up to and including 7
    """
    if interactive and not taskid:
        deleteinteractive()
    else:
        if not taskid:
            console.print("[bold red]Error: Task ID or range required.[/]")
            return

        # Check if it's a range specification
        if ":" in taskid:
            deleterange(taskid, force)
        else:
            try:
                task_number = int(taskid)
                _deletetask(task_number, force)
            except ValueError:
                console.print(f"[bold red]Invalid task ID: {taskid}[/]")
                console.print("Use a single number (e.g., 2) or a range (e.g., 2:5, 2:, :7)")


def deleteinteractive():
    """Delete a task with interactive selection."""
    # Get tasks - use includeall=True as a fallback if pending filter fails
    tasks = tasklist(includeall=True)

    # Filter to show only pending tasks in the UI (but we've already fetched all to work around TaskWarrior issues)
    pending_tasks = [task for task in tasks if task.status == "pending"]

    # Display tasks
    if pending_tasks:
        printtasktable(pending_tasks, "Pending Tasks")
    else:
        # If no pending tasks, show all tasks as a fallback
        printtasktable(tasks, "All Tasks")
        if not tasks:
            console.print("[yellow]No tasks found. Nothing to delete.[/]")
            return

    # Set up questionary style
    style = questionary.Style.from_dict(getstyle())

    # Add options for range-based deletion
    display_tasks = pending_tasks if pending_tasks else tasks

    delete_options = [
        questionary.Choice("Delete a single task", "single"),
        questionary.Choice("Delete a range of tasks", "range"),
        questionary.Choice("Delete all displayed tasks", "all")
    ]

    delete_type = questionary.select(
        "What would you like to delete?",
        choices=delete_options,
        style=style
    ).ask()

    if delete_type == "single":
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
            "Select a task to delete:",
            choices=choices,
            style=style
        ).ask()

        if taskid:
            _deletetask(taskid)

    elif delete_type == "range":
        # Get the min and max task IDs
        valid_ids = sorted([task.id for task in display_tasks if task.id is not None])
        if not valid_ids:
            console.print("[yellow]No valid task IDs found.[/]")
            return

        min_id, max_id = min(valid_ids), max(valid_ids)

        # Get range start
        start_id = questionary.text(
            f"Enter start of range (min: {min_id}, leave blank for {min_id}):",
            default=str(min_id),
            style=style
        ).ask()

        try:
            start = int(start_id) if start_id.strip() else min_id
        except ValueError:
            console.print(f"[yellow]Invalid start ID, using {min_id}.[/]")
            start = min_id

        # Get range end
        end_id = questionary.text(
            f"Enter end of range (max: {max_id}, leave blank for {max_id}):",
            default=str(max_id),
            style=style
        ).ask()

        try:
            end = int(end_id) if end_id.strip() else max_id
        except ValueError:
            console.print(f"[yellow]Invalid end ID, using {max_id}.[/]")
            end = max_id

        # Delete the range
        deleterange(f"{start}:{end}")

    elif delete_type == "all":
        # Get confirmation for deleting all tasks
        task_ids = [task.id for task in display_tasks if task.id is not None]

        if not task_ids:
            console.print("[yellow]No valid task IDs found.[/]")
            return

        count = len(task_ids)
        console.print(f"[bold]This will delete {count} tasks:[/]")

        # Generate a preview of tasks to delete
        preview_tasks = display_tasks[:5]  # Show first 5 tasks
        printtasktable(preview_tasks, "Preview of tasks to delete")

        if count > 5:
            console.print(f"[bold]...and {count - 5} more tasks[/]")

        # Confirm deletion
        confirm = confirmaction(f"[bold red]Delete all {count} tasks?[/] This cannot be undone!")

        if confirm:
            success_count = 0
            for task_id in task_ids:
                if deletetask(task_id):
                    success_count += 1

            console.print(f"[bold green]Successfully deleted {success_count}/{count} tasks.[/]")
        else:
            console.print("Task deletion cancelled.")


def deleterange(range_spec: str, force: bool = False):
    """Delete a range of tasks specified by 'start:end'."""
    # Parse the range specification
    match = re.match(r"^(\d+)?:(\d+)?$", range_spec)
    if not match:
        console.print(f"[bold red]Invalid range format: {range_spec}[/]")
        console.print("Use format like '2:5', '2:', or ':7'")
        return

    start_str, end_str = match.groups()

    # Get all tasks
    tasks = tasklist(includeall=True)

    # Collect task IDs
    task_ids = sorted([task.id for task in tasks if task.id is not None])

    if not task_ids:
        console.print("[yellow]No tasks found.[/]")
        return

    # Determine start and end points
    start = int(start_str) if start_str else min(task_ids)
    end = int(end_str) if end_str else max(task_ids)

    # Filter to tasks in the range
    to_delete = [id for id in task_ids if start <= id <= end]

    if not to_delete:
        console.print(f"[yellow]No tasks found in range {range_spec}.[/]")
        return

    # Show tasks to be deleted
    range_tasks = [task for task in tasks if task.id in to_delete]
    printtasktable(range_tasks, f"Tasks to delete ({range_spec})")

    # Confirm deletion if not forced
    if not force:
        confirmed = confirmaction(
            f"[bold red]Delete {len(to_delete)} tasks in range {range_spec}?[/]\n"
            "This action cannot be undone!"
        )

        if not confirmed:
            console.print("Task deletion cancelled.")
            return

    # Delete tasks
    success_count = 0
    for task_id in to_delete:
        if deletetask(task_id):
            success_count += 1

    console.print(f"[bold green]Successfully deleted {success_count}/{len(to_delete)} tasks.[/]")


def _deletetask(taskid: int, force: bool = False):
    """Delete the specified task."""
    # Get task details
    task = gettask(taskid)

    if not task:
        console.print(f"[bold red]Task {taskid} not found.[/]")
        return

    # Confirm deletion
    if not force:
        confirmed = confirmaction(
            f"[bold red]Delete task {taskid}: {task.description}?[/]\n"
            "This action cannot be undone!"
        )

        if not confirmed:
            console.print("Task deletion cancelled.")
            return

    # Delete task
    success = deletetask(taskid)

    if success:
        console.print(f"[bold green]Task {taskid} deleted successfully.[/]")
    else:
        console.print(f"[bold red]Failed to delete task {taskid}.[/]")
