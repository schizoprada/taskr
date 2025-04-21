# ~/taskr/src/taskr/cli/commands/repeat.py
"""
Repeat task command.

This module provides functionality to repeat tasks at specified intervals.
"""

import typer
import questionary
import datetime
from typing import Optional, List
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse, ParserError
import re

from taskr.logs import log
from taskr.interface import gettask, addtask, tasklist
from taskr.cli.common import console, getstyle, printtasktable, confirmaction

# Create command app
app = typer.Typer()


@app.callback(invoke_without_command=True)
def repeatcallback(
        taskid: Optional[int] = typer.Argument(
            None, help="Task ID to repeat"
        ),
        frequency: Optional[str] = typer.Option(
            None, "--frequency", "-f",
            help="Frequency (daily, weekly, monthly, yearly)"
        ),
        times: Optional[int] = typer.Option(
            None, "--times", "-t",
            help="Number of times to repeat the task"
        ),
        until: Optional[str] = typer.Option(
            None, "--until", "-u",
            help="Date to repeat until (YYYY-MM-DD or relative like 'next month')"
        ),
        interval: Optional[int] = typer.Option(
            1, "--interval", "-i",
            help="Interval between repetitions (e.g., every 2 weeks)"
        ),
        interactive: bool = typer.Option(
            True, "--interactive/--no-interactive", help="Use interactive mode"
        )
    ):
    """
    Repeat a task with specified frequency.

    Examples:
        taskr repeat 1 --frequency daily --until "next month"
        taskr repeat 2 --frequency weekly --times 8
        taskr repeat 3 --frequency monthly --until "end of year"
    """
    if interactive or not taskid:
        repeatinteractive()
    else:
        _repeattask(taskid, frequency, times, until, interval)


def repeatinteractive():
    """Repeat a task with interactive prompts."""
    # Set up questionary style
    style = questionary.Style.from_dict(getstyle())

    # Get all active tasks instead of just pending to handle TaskWarrior filtering issues
    tasks = tasklist(includeall=True, includedeleted=False)

    # Filter to pending tasks in Python
    pending_tasks = [task for task in tasks if task.status == "pending"]

    # Display tasks
    if pending_tasks:
        printtasktable(pending_tasks, "Pending Tasks")
    else:
        console.print("[yellow]No pending tasks found.[/]")
        return

    if not pending_tasks:
        return

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
        "Select a task to repeat:",
        choices=choices,
        style=style
    ).ask()

    if not taskid:
        return

    # Simplified frequency selection with better labels
    frequency_choices = [
        questionary.Choice("Daily", "daily"),
        questionary.Choice("Weekly", "weekly"),
        questionary.Choice("Monthly", "monthly"),
        questionary.Choice("Yearly", "yearly")
    ]

    frequency = questionary.select(
        "How often to repeat?",
        choices=frequency_choices,
        style=style
    ).ask()

    # Ask if user wants to customize the interval
    customize_interval = questionary.confirm(
        f"Customize the {frequency} interval?",
        default=False,
        style=style
    ).ask()

    interval = 1  # default
    if customize_interval:
        interval_str = questionary.text(
            f"Repeat every how many {frequency} periods?",
            default="1",
            style=style
        ).ask()

        try:
            interval = int(interval_str)
            if interval < 1:
                console.print("[yellow]Interval must be at least 1, using 1 instead.[/]")
                interval = 1
        except ValueError:
            console.print("[yellow]Invalid interval, using 1 instead.[/]")
            interval = 1

    # Prompt for repetition approach
    repetition_type = questionary.select(
        "How long to repeat?",
        choices=[
            "Until a specific date",
            "For a set number of occurrences"
        ],
        style=style
    ).ask()

    times = None
    until = None

    if repetition_type == "For a set number of occurrences":
        times_input = questionary.text(
            "How many occurrences?",
            default="5",
            style=style
        ).ask()

        try:
            times = int(times_input)
            if times < 1:
                console.print("[yellow]Number must be at least 1, using 1 instead.[/]")
                times = 1
        except ValueError:
            console.print("[yellow]Invalid number, using 5 instead.[/]")
            times = 5
    else:
        # Provide common choices for 'until' date
        until_choices = [
            questionary.Choice("Next week", "next week"),
            questionary.Choice("End of month", "end of month"),
            questionary.Choice("Next month", "next month"),
            questionary.Choice("3 months from now", "3 months"),
            questionary.Choice("6 months from now", "6 months"),
            questionary.Choice("End of year", "end of year"),
            questionary.Choice("Custom date...", "custom")
        ]

        until_result = questionary.select(
            "Repeat until when?",
            choices=until_choices,
            style=style
        ).ask()

        if until_result == "custom":
            until = questionary.text(
                "Enter end date (YYYY-MM-DD or relative like 'next month'):",
                style=style
            ).ask()
        elif until_result == "3 months":
            # Handle special cases
            until = "now+3months"
        elif until_result == "6 months":
            until = "now+6months"
        else:
            until = until_result

    # Repeat task
    _repeattask(taskid, frequency, times, until, interval)

def _repeattask(taskid: int, frequency: str, times: Optional[int] = None,
                until: Optional[str] = None, interval: int = 1):
    """
    Repeat a task with the given parameters.

    Args:
        taskid: ID of the task to repeat
        frequency: How often to repeat (daily, weekly, monthly, yearly)
        times: Number of times to repeat (exclusive with until)
        until: Date to repeat until (exclusive with times)
        interval: Interval between repetitions
    """
    # Validate parameters
    if not frequency:
        console.print("[bold red]Frequency must be specified.[/]")
        return

    if frequency not in ["daily", "weekly", "monthly", "yearly"]:
        console.print(f"[bold red]Invalid frequency: {frequency}[/]")
        console.print("Valid options are: daily, weekly, monthly, yearly")
        return

    if not times and not until:
        console.print("[bold red]Either times or until must be specified.[/]")
        return

    if times and until:
        console.print("[yellow]Both times and until specified. Using times.[/]")
        until = None

    # Get the original task
    original_task = gettask(taskid)
    if not original_task:
        console.print(f"[bold red]Task {taskid} not found.[/]")
        return

    # Parse the due date from the original task
    if not original_task.due:
        console.print("[bold red]Original task must have a due date to repeat.[/]")
        return

    # Parse the original due date
    try:
        original_due = parse_date(original_task.due)
    except Exception as e:
        console.print(f"[bold red]Error parsing original due date: {str(e)}[/]")
        return

    # Calculate the end date if 'until' is specified
    end_date = None
    if until:
        try:
            end_date = parse_relative_date(until)
            console.print(f"Will repeat until: [cyan]{end_date.strftime('%Y-%m-%d')}[/]")
        except Exception as e:
            console.print(f"[bold red]Error parsing 'until' date: {str(e)}[/]")
            return

    # Determine how many tasks to create
    repetitions = times if times else 100  # Use a large number if until is specified
    created_count = 0
    last_due_date = original_due

    # Create repeated tasks
    new_task_ids = []
    for i in range(repetitions):
        # Calculate next due date
        next_due = calculate_next_date(last_due_date, frequency, interval)
        last_due_date = next_due

        # If using 'until', check if we've passed the end date
        if end_date and next_due.date() > end_date.date():  # Compare only the date parts
            break

        # Create the new task with the same properties but updated due date
        formatted_due = next_due.strftime("%Y-%m-%d")

        # Add the repeated task
        new_task = addtask(
            description=original_task.description,
            project=original_task.project,
            priority=original_task.priority,
            tags=original_task.tags,
            due=formatted_due,
            scheduled=original_task.scheduled,
            wait=original_task.wait,
            depends=original_task.depends
        )

        if new_task:
            new_task_ids.append(new_task.id)
            created_count += 1
        else:
            console.print(f"[bold red]Failed to create repeated task #{i+1}.[/]")

    # Show summary
    if created_count > 0:
        console.print(f"[bold green]Created {created_count} repeated tasks based on task {taskid}.[/]")
        console.print(f"New task IDs: {', '.join([str(id) for id in new_task_ids])}")
    else:
        console.print("[bold red]No repeated tasks were created.[/]")


def parse_date(date_str: str) -> datetime.datetime:
    """Parse a date string in TaskWarrior format."""
    try:
        # Try parsing as YYYYMMDD
        if len(date_str) == 8 and date_str.isdigit():
            year = int(date_str[0:4])
            month = int(date_str[4:6])
            day = int(date_str[6:8])
            return datetime.datetime(year, month, day)

        # Try parsing as ISO format (YYYY-MM-DD)
        elif len(date_str) == 10 and date_str[4] == '-' and date_str[7] == '-':
            year = int(date_str[0:4])
            month = int(date_str[5:7])
            day = int(date_str[8:10])
            return datetime.datetime(year, month, day)

        # Handle TaskWarrior timestamp format (with T separator)
        elif 'T' in date_str:
            date_part = date_str.split('T')[0]
            if len(date_part) == 8:  # YYYYMMDD
                year = int(date_part[0:4])
                month = int(date_part[4:6])
                day = int(date_part[6:8])
                return datetime.datetime(year, month, day)

        # If none of the above, try dateutil parser
        dt = parse(date_str)
        # Ensure naive datetime (no timezone)
        if dt.tzinfo is not None:
            dt = dt.replace(tzinfo=None)
        return dt
    except Exception as e:
        log.error(f"Error parsing date {date_str}: {str(e)}")
        # Default to today if parsing fails
        console.print(f"[yellow]Could not parse date '{date_str}', using today instead.[/]")
        return datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)


def parse_relative_date(date_str: str) -> datetime.datetime:
    """
    Parse a relative date string.

    Examples:
        "next week", "end of month", "tomorrow", "2023-12-31"
    """
    today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # Handle special case for 'now+X' format
    if date_str.startswith('now+'):
        try:
            parts = date_str[4:].split('months')
            if len(parts) == 2 and parts[0].strip().isdigit():
                months = int(parts[0].strip())
                return today + relativedelta(months=months)
        except Exception:
            pass

    # First try direct parsing (for YYYY-MM-DD format)
    try:
        dt = parse(date_str)
        # Ensure naive datetime (no timezone)
        if dt.tzinfo is not None:
            dt = dt.replace(tzinfo=None)
        return dt
    except ParserError:
        pass

    # Handle special cases
    normalized = date_str.lower().strip()

    # Check for mm/dd format
    if re.match(r"^\d{1,2}/\d{1,2}$", normalized):
        month, day = map(int, normalized.split('/'))
        year = today.year
        # If the date has already passed this year, assume next year
        try:
            date = datetime.datetime(year, month, day)
            if date < today:
                date = datetime.datetime(year + 1, month, day)
            return date
        except ValueError:
            raise ValueError(f"Invalid date: {date_str}")

    # Handle relative dates
    if "tomorrow" in normalized:
        return today + datetime.timedelta(days=1)
    elif "next week" in normalized:
        return today + datetime.timedelta(days=7)
    elif "next month" in normalized:
        return today + relativedelta(months=1)
    elif "3 months" in normalized:
        return today + relativedelta(months=3)
    elif "6 months" in normalized:
        return today + relativedelta(months=6)
    elif "end of month" in normalized:
        return today.replace(day=1) + relativedelta(months=1, days=-1)
    elif "end of year" in normalized:
        return datetime.datetime(today.year, 12, 31)
    elif "next year" in normalized:
        return today + relativedelta(years=1)

    # If we can't parse it, raise an error
    raise ValueError(f"Could not parse relative date: {date_str}")


def calculate_next_date(current_date: datetime.datetime, frequency: str, interval: int = 1) -> datetime.datetime:
    """Calculate the next date based on frequency and interval."""
    # Ensure current_date has no timezone
    if current_date.tzinfo is not None:
        current_date = current_date.replace(tzinfo=None)

    if frequency == "daily":
        return current_date + datetime.timedelta(days=interval)
    elif frequency == "weekly":
        return current_date + datetime.timedelta(weeks=interval)
    elif frequency == "monthly":
        return current_date + relativedelta(months=interval)
    elif frequency == "yearly":
        return current_date + relativedelta(years=interval)
    else:
        raise ValueError(f"Invalid frequency: {frequency}")
