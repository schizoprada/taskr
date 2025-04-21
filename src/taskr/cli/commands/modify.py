# ~/taskr/src/taskr/cli/commands/modify.py
"""
Modify task command.

This module provides the command for modifying tasks.
"""

import typer
import questionary
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from taskr.interface import modifytask, tasklist, gettask
from taskr.cli.common import console, getstyle, printtasktable, printtaskdetails, Priority

# Create command app
app = typer.Typer()


@app.callback(invoke_without_command=True)
def modifycallback(
    taskid: Optional[int] = typer.Argument(
        None, help="Task ID to modify"
    ),
    description: Optional[str] = typer.Option(
        None, "--description", "-d", help="New task description"
    ),
    project: Optional[str] = typer.Option(
        None, "--project", "-p", help="New project name"
    ),
    priority: Optional[Priority] = typer.Option(
        None, "--priority", "-P", help="New task priority (H, M, L)"
    ),
    addtags: Optional[List[str]] = typer.Option(
        None, "--add-tag", "+t", help="Tags to add"
    ),
    removetags: Optional[List[str]] = typer.Option(
        None, "--remove-tag", "-t", help="Tags to remove"
    ),
    due: Optional[str] = typer.Option(
        None, "--due", help="New due date (YYYY-MM-DD or relative like 'tomorrow')"
    ),
    cleardue: bool = typer.Option(
        False, "--clear-due", help="Clear due date"
    ),
    scheduled: Optional[str] = typer.Option(
        None, "--scheduled", help="New scheduled date"
    ),
    clearscheduled: bool = typer.Option(
        False, "--clear-scheduled", help="Clear scheduled date"
    ),
    wait: Optional[str] = typer.Option(
        None, "--wait", help="New wait date"
    ),
    clearwait: bool = typer.Option(
        False, "--clear-wait", help="Clear wait date"
    ),
    depends: Optional[str] = typer.Option(
        None, "--depends", help="New dependencies"
    ),
    cleardepends: bool = typer.Option(
        False, "--clear-depends", help="Clear dependencies"
    ),
    annotation: Optional[str] = typer.Option(
        None, "--annotation", "-a", help="Add annotation"
    ),
    interactive: bool = typer.Option(
        True, "--interactive/--no-interactive", "-i", help="Use interactive mode"
    )
):
    """
    Modify a task.

    By default uses interactive mode. Use --no-interactive to modify using command-line options.
    """
    if interactive or not taskid:
        modifyinteractive()
    else:
        # Process clear options
        if cleardue:
            due = ""
        if clearscheduled:
            scheduled = ""
        if clearwait:
            wait = ""
        if cleardepends:
            depends = ""

        # Format dates
        formatteddue = _formatdate(due) if due is not None else None
        formattedscheduled = _formatdate(scheduled) if scheduled is not None else None
        formattedwait = _formatdate(wait) if wait is not None else None

        # Create annotations list
        annotations = [annotation] if annotation else None

        # Modify task
        _modifytask(
            taskid,
            description=description,
            project=project,
            priority=priority,
            tagsadd=addtags,
            tagsremove=removetags,
            due=formatteddue,
            scheduled=formattedscheduled,
            wait=formattedwait,
            depends=depends,
            annotations=annotations
        )


def modifyinteractive():
    """Modify a task with interactive selection and prompts."""
    # Get tasks - use all=True as a fallback if pending filter fails
    tasks = tasklist(includeall=True)

    # Filter to show only pending tasks in the UI
    pending_tasks = [task for task in tasks if task.status == "pending"]

    # Display tasks
    if pending_tasks:
        printtasktable(pending_tasks, "Pending Tasks")
    else:
        console.print("[yellow]No pending tasks found. Nothing to modify.[/yellow]")
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
        "Select a task to modify:",
        choices=choices,
        style=style
    ).ask()

    if not taskid:
        return

    # Get task details
    task = gettask(taskid)

    if not task:
        console.print(f"[bold red]Task {taskid} not found.[/bold red]")
        return

    # Display current task details
    printtaskdetails(task)

    # Prompt for modifications
    modifications = {}

    # Description
    if questionary.confirm(
        "Modify description?",
        default=False,
        style=style
    ).ask():
        description = questionary.text(
            "New description:",
            default=task.description,
            style=style
        ).ask()
        modifications["description"] = description

    # Project
    if questionary.confirm(
        "Modify project?",
        default=False,
        style=style
    ).ask():
        project = questionary.text(
            "New project:",
            default=task.project or "",
            style=style
        ).ask()
        modifications["project"] = project

    # Priority
    if questionary.confirm(
        "Modify priority?",
        default=False,
        style=style
    ).ask():
        priority = questionary.select(
            "New priority:",
            choices=[
                questionary.Choice("High (H)", "H"),
                questionary.Choice("Medium (M)", "M"),
                questionary.Choice("Low (L)", "L"),
                questionary.Choice("None", "")
            ],
            default=task.priority or "",
            style=style
        ).ask()
        modifications["priority"] = priority

    # Tags
    if questionary.confirm(
        "Modify tags?",
        default=False,
        style=style
    ).ask():
        currenttags = ", ".join(task.tags) if task.tags else ""
        tagsinput = questionary.text(
            "New tags (comma-separated):",
            default=currenttags,
            style=style
        ).ask()

        # Calculate tags to add and remove
        newtags = [tag.strip() for tag in tagsinput.split(",")] if tagsinput else []
        oldtags = task.tags or []

        tagsadd = [tag for tag in newtags if tag and tag not in oldtags]
        tagsremove = [tag for tag in oldtags if tag not in newtags]

        if tagsadd:
            modifications["tagsadd"] = tagsadd
        if tagsremove:
            modifications["tagsremove"] = tagsremove

    # Due date
    if questionary.confirm(
        "Modify due date?",
        default=False,
        style=style
    ).ask():
        duechoices = [
            questionary.Choice("None", ""),
            questionary.Choice("Today", "today"),
            questionary.Choice("Tomorrow", "tomorrow"),
            questionary.Choice("Next week", "1week"),
            questionary.Choice("Custom date", "custom")
        ]

        dueoption = questionary.select(
            "New due date:",
            choices=duechoices,
            style=style
        ).ask()

        if dueoption == "custom":
            due = questionary.text(
                "Enter due date (YYYY-MM-DD):",
                default=task.due or "",
                style=style
            ).ask()
        else:
            due = dueoption

        modifications["due"] = _formatdate(due) if due else ""

    # Scheduled date
    if questionary.confirm(
        "Modify scheduled date?",
        default=False,
        style=style
    ).ask():
        scheduledchoices = [
            questionary.Choice("None", ""),
            questionary.Choice("Today", "today"),
            questionary.Choice("Tomorrow", "tomorrow"),
            questionary.Choice("Next week", "1week"),
            questionary.Choice("Custom date", "custom")
        ]

        scheduledoption = questionary.select(
            "New scheduled date:",
            choices=scheduledchoices,
            style=style
        ).ask()

        if scheduledoption == "custom":
            scheduled = questionary.text(
                "Enter scheduled date (YYYY-MM-DD):",
                default=task.scheduled or "",
                style=style
            ).ask()
        else:
            scheduled = scheduledoption

        modifications["scheduled"] = _formatdate(scheduled) if scheduled else ""

    # Annotation
    if questionary.confirm(
        "Add annotation?",
        default=False,
        style=style
    ).ask():
        annotation = questionary.text(
            "Enter annotation:",
            style=style
        ).ask()

        if annotation:
            modifications["annotations"] = [annotation]

    # Modify task
    if modifications:
        _modifytask(taskid, **modifications)
    else:
        console.print("No modifications made.")


def _modifytask(
    taskid: int,
    **kwargs
):
    """Modify the specified task with the given attributes."""
    # Get task details
    task = gettask(taskid)

    if not task:
        console.print(f"[bold red]Task {taskid} not found.[/bold red]")
        return

    # Modify task
    modifiedtask = modifytask(taskid, **kwargs)

    if modifiedtask:
        console.print(f"[bold green]Task {taskid} modified successfully.[/bold green]")
        printtaskdetails(modifiedtask)
    else:
        console.print(f"[bold red]Failed to modify task {taskid}.[/bold red]")


def _formatdate(datestr: str) -> str:
    """Format date string for TaskWarrior."""
    if not datestr:
        return ""

    # Handle relative dates
    if datestr == "today":
        return datetime.now().strftime("%Y-%m-%d")
    elif datestr == "tomorrow":
        return (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    elif datestr.endswith("week"):
        try:
            weeks = int(datestr[0])
            return (datetime.now() + timedelta(weeks=weeks)).strftime("%Y-%m-%d")
        except (ValueError, IndexError):
            return datestr
    elif datestr.endswith("day") or datestr.endswith("days"):
        try:
            days = int(datestr.split()[0])
            return (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
        except (ValueError, IndexError):
            return datestr

    # Return as is for already formatted dates
    return datestr
