# ~/taskr/src/taskr/cli/common.py
"""
Common utilities for CLI commands.

This module provides shared functions and styles for CLI commands.
"""

import typing as t
import datetime
from enum import Enum
import questionary
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from taskr.config import getconfig
from taskr.interface import Task


# Console for rich output
console = Console()


# Priority options
class Priority(str, Enum):
    HIGH = "H"
    MEDIUM = "M"
    LOW = "L"
    NONE = ""


# Common styles for questionary prompts
def getstyle():
    """Get questionary style based on configuration."""
    theme = getconfig("display", "theme")

    if theme == "dark":
        return {
            "question": "#FF875F bold",
            "answer": "#AFFFFF bold",
            "pointer": "#FF5F87",
            "highlighted": "#5F87FF",
            "instruction": "#767676",
            "text": "#DADADA",
        }
    else:
        return {
            "question": "#FF5F00 bold",
            "answer": "#005FFF bold",
            "pointer": "#FF005F",
            "highlighted": "#005FFF",
            "instruction": "#767676",
            "text": "#303030",
        }


def formatdate(date: t.Optional[str]) -> str:
    """Format date for display."""
    if not date:
        return ""

    # Remove timezone info if present
    if "T" in date:
        date = date.split("T")[0]

    # Parse and format date
    try:
        dateformat = getconfig("display", "date.format")
        dateobj = datetime.datetime.strptime(date, "%Y%m%d")

        if dateformat == "YYYY-MM-DD":
            return dateobj.strftime("%Y-%m-%d")
        elif dateformat == "MM/DD/YYYY":
            return dateobj.strftime("%m/%d/%Y")
        elif dateformat == "DD/MM/YYYY":
            return dateobj.strftime("%d/%m/%Y")
        else:
            return date
    except Exception:
        return date


def getprioritycolor(priority: t.Optional[str]) -> str:
    """Get color for priority level."""
    if not priority:
        priority = ""

    colors = getconfig("display", "prioritycolors") or {
        "H": "red",
        "M": "yellow",
        "L": "blue",
        "": "white"
    }

    return colors.get(priority, "white")


def printtasktable(tasks: t.List[Task], title: str = "Tasks"):
    """Print a formatted table of tasks."""
    if not tasks:
        console.print(f"No {title.lower()} found that match your filters.")
        return

    # Create table
    table = Table(title=title)

    # Add columns
    table.add_column("ID", style="cyan")
    table.add_column("Description")
    table.add_column("Project", style="green")
    table.add_column("Status", style="yellow")  # New status column
    table.add_column("Due", style="magenta")
    table.add_column("Priority")

    if getconfig("display", "showtags"):
        table.add_column("Tags", style="blue")

    # Add rows
    for task in tasks:
        # Format due date
        duedate = formatdate(task.due)

        # Format priority with color
        prioritycolor = getprioritycolor(task.priority)
        priority = Text(task.priority or "", style=prioritycolor)

        # Format tags
        tags = ", ".join(task.tags) if task.tags else ""

        # Format status with color
        statuscolors = {
            "pending": "green",
            "completed": "blue",
            "deleted": "red",
            "waiting": "yellow"
        }
        statuscolor = statuscolors.get(task.status, "white")
        status = Text(task.status or "", style=statuscolor)

        # Add row
        if getconfig("display", "showtags"):
            table.add_row(
                str(task.id),
                task.description,
                task.project or "",
                status,  # Add status column
                duedate,
                priority,
                tags
            )
        else:
            table.add_row(
                str(task.id),
                task.description,
                task.project or "",
                status,  # Add status column
                duedate,
                priority
            )

    # Print table
    console.print(table)


def printtaskdetails(task: Task):
    """Print detailed information about a task."""
    if not task:
        console.print("Task not found.")
        return

    # Create panel
    panel = Panel(
        f"[bold cyan]ID:[/bold cyan] {task.id}\n"
        f"[bold cyan]UUID:[/bold cyan] {task.uuid}\n"
        f"[bold cyan]Description:[/bold cyan] {task.description}\n"
        f"[bold cyan]Status:[/bold cyan] {task.status}\n"
        f"[bold cyan]Project:[/bold cyan] {task.project or ''}\n"
        f"[bold cyan]Priority:[/bold cyan] [bold {getprioritycolor(task.priority)}]{task.priority or ''}[/]\n"
        f"[bold cyan]Tags:[/bold cyan] {', '.join(task.tags) if task.tags else ''}\n"
        f"[bold cyan]Due:[/bold cyan] {formatdate(task.due) if task.due else ''}\n"
        f"[bold cyan]Scheduled:[/bold cyan] {formatdate(task.scheduled) if task.scheduled else ''}\n"
        f"[bold cyan]Wait:[/bold cyan] {formatdate(task.wait) if task.wait else ''}\n"
        f"[bold cyan]Entry:[/bold cyan] {formatdate(task.entry) if task.entry else ''}\n"
        f"[bold cyan]Modified:[/bold cyan] {formatdate(task.modified) if task.modified else ''}\n"
        f"[bold cyan]Start:[/bold cyan] {formatdate(task.start) if task.start else ''}\n"
        f"[bold cyan]End:[/bold cyan] {formatdate(task.end) if task.end else ''}\n"
        f"[bold cyan]Urgency:[/bold cyan] {task.urgency if task.urgency is not None else ''}",
        title=f"Task {task.id}",
        expand=False
    )

    # Print panel
    console.print(panel)

    # Print annotations
    if task.annotations:
        console.print("[bold cyan]Annotations:[/bold cyan]")
        for annotation in task.annotations:
            console.print(f"  • {annotation.get('description', '')}")

    # Print UDAs
    if task.udas:
        console.print("[bold cyan]User Defined Attributes:[/bold cyan]")
        for key, value in task.udas.items():
            console.print(f"  • [bold]{key}:[/] {value}")


def confirmaction(message: str) -> bool:
    """Confirm an action with the user."""
    result = questionary.confirm(
        message,
        style=questionary.Style.from_dict(getstyle())
    ).ask()

    return result
