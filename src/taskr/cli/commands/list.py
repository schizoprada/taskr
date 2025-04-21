# ~/taskr/src/taskr/cli/commands/list.py
"""
List tasks command.

This module provides the command for listing tasks.
"""

import typer
import questionary
from typing import Optional, List
import datetime
from taskr.logs import log
from taskr.config import getconfig
from taskr.interface import tasklist
from taskr.cli.common import console, getstyle, printtasktable

# Create command app
app = typer.Typer()


@app.callback(invoke_without_command=True)
def listcallback(
        project: Optional[str] = typer.Option(
            None, "--project", "-p", help="Filter by project"
        ),
        tags: Optional[List[str]] = typer.Option(
            None, "--tag", "-t", help="Filter by tags"
        ),
        priority: Optional[str] = typer.Option(
            None, "--priority", "-P", help="Filter by priority (H, M, L)"
        ),
        status: Optional[str] = typer.Option(
            None, "--status", "-s", help="Filter by status (pending, completed, deleted)"
        ),
        all: bool = typer.Option(
            False, "--all", "-a", help="Show all tasks, including completed and deleted"
        ),
        filter: Optional[str] = typer.Option(
            None, "--filter", "-f", help="Use a saved filter"
        ),
        interactive: bool = typer.Option(
            True, "--interactive/--no-interactive", "-i/-ni", help="Use interactive mode"
        )
    ):
    """
    List tasks from TaskWarrior.

    By default uses interactive mode. Use --no-interactive to filter using command-line options.
    """
    if interactive:
        listinteractive()
    else:
        filterargs = []

        if filter:
            # Use saved filter
            savedfilters = getconfig("filters", "savedfilters") or {}
            filterargs = savedfilters.get(filter, [])
        else:
            # Use command-line filters
            if status:
                filterargs.append(f"status:{status}")

            # Add any additional filter arguments
            if project:
                filterargs.append(f"project:{project}")

        # Get tasks
        tasks = tasklist(
            filterargs=filterargs,
            status=status if not filter else None,
            project=project if not filter else None,
            tags=tags,
            priority=priority,
            includeall=all
        )

        # Display tasks
        printtasktable(tasks)


@app.command("today")
def listtoday():
    """List tasks due or scheduled for today."""
    # Use saved filter if available
    savedfilters = getconfig("filters", "savedfilters") or {}
    filterargs = savedfilters.get("today", ["+SCHEDULED", "+TODAY", "or", "+DUE", "+TODAY"])

    # Get tasks
    tasks = tasklist(filterargs=filterargs)

    # Display tasks
    printtasktable(tasks, "Today's Tasks")


@app.command("week")
def listweek():
    """List tasks due or scheduled for this week."""
    tasks = tasklist(filterargs=["+SCHEDULED", "+WEEK", "or", "+DUE", "+WEEK"])
    printtasktable(tasks, "This Week's Tasks")


@app.command("overdue")
def listoverdue():
    """List overdue tasks."""
    tasks = tasklist(filterargs=["+OVERDUE"])
    printtasktable(tasks, "Overdue Tasks")


@app.command("completed")
def listcompleted():
    """List recently completed tasks."""
    tasks = tasklist(status="completed")
    printtasktable(tasks, "Completed Tasks")


def listinteractive():
    """List tasks with interactive filtering."""
    # Set up questionary style
    style = questionary.Style.from_dict(getstyle())

    # Get initial filter choices
    mainfilterchoices = [
        questionary.Choice("Quick Filters", "quick"),
        questionary.Choice("Filter by Date", "date"),
        questionary.Choice("Filter by Project", "project"),
        questionary.Choice("Filter by Tags", "tags"),
        questionary.Choice("Filter by Priority", "priority"),
        questionary.Choice("Filter by Status", "status"),
        questionary.Choice("Advanced Filter", "advanced")
    ]

    # Prompt for main filter type
    filtertype = questionary.select(
        "How would you like to filter tasks?",
        choices=mainfilterchoices,
        style=style
    ).ask()

    if filtertype == "quick":
        # Get saved filters
        savedfilters = getconfig("filters", "savedfilters") or {}
        filterchoices = [
            questionary.Choice("All pending tasks", "pending"),
            questionary.Choice("Today's tasks", "today"),
            questionary.Choice("Tomorrow's tasks", "tomorrow"),
            questionary.Choice("This week's tasks", "week"),
            questionary.Choice("Overdue tasks", "overdue"),
            questionary.Choice("Recently completed", "completed"),
            questionary.Choice("All active tasks", "all"),
            questionary.Choice("All tasks (including deleted)", "all-with-deleted")
        ]

        # Add user-defined filters
        for name in savedfilters.keys():
            if name not in ["today", "week", "overdue"]:
                filterchoices.append(questionary.Choice(f"Filter: {name}", name))

        # Prompt for filter
        filterchoice = questionary.select(
            "Select tasks to display:",
            choices=filterchoices,
            style=style
        ).ask()

        # Apply quick filter
        applyquickfilter(filterchoice)

    elif filtertype == "date":
        # Date filter options
        datechoices = [
            questionary.Choice("Due today", "due:today"),
            questionary.Choice("Due tomorrow", "due:tomorrow"),
            questionary.Choice("Due this week", "due:week"),
            questionary.Choice("Due next week", "due:eow+7d"),
            questionary.Choice("Due this month", "due:month"),
            questionary.Choice("Overdue", "+OVERDUE"),
            questionary.Choice("No due date", "due:"),
            questionary.Choice("Custom date range", "custom")
        ]

        # Prompt for date filter
        selecteddate = questionary.select(
            "Select date filter:",
            choices=datechoices,
            style=style
        ).ask()

        if selecteddate == "custom":
            # Get custom date range
            startdate = questionary.text(
                "Start date (YYYY-MM-DD or relative like 'today', 'tomorrow', blank for no start):",
                style=style
            ).ask()

            enddate = questionary.text(
                "End date (YYYY-MM-DD or relative like 'today', 'tomorrow', blank for no end):",
                style=style
            ).ask()

            # Build filter args
            filterargs = []
            if startdate:
                filterargs.append(f"due.after:{startdate}")
            if enddate:
                filterargs.append(f"due.before:{enddate}")

            if filterargs:
                tasks = tasklist(filterargs=filterargs)
                daterange = f"{startdate or 'any'} to {enddate or 'any'}"
                printtasktable(tasks, f"Due date range: {daterange}")
            else:
                console.print("[yellow]No date range specified.[/]")

        elif selecteddate:
            # For predefined date filters
            tasks = tasklist(filterargs=[selecteddate])

            # Map filter to display name
            filternames = {
                "due:today": "Due today",
                "due:tomorrow": "Due tomorrow",
                "due:week": "Due this week",
                "due:eow+7d": "Due next week",
                "due:month": "Due this month",
                "+OVERDUE": "Overdue",
                "due:": "No due date"
            }

            title = filternames.get(selecteddate, selecteddate)
            printtasktable(tasks, title)

    elif filtertype == "project":
        # Get all projects from tasks
        alltasks = tasklist(includeall=True, includedeleted=False)
        projects = sorted(list(set([task.project for task in alltasks if task.project])))

        if not projects:
            console.print("[yellow]No projects found in tasks.[/]")
            return

        # Add "All Projects" option
        projectchoices = [questionary.Choice("All Projects", None)]
        projectchoices.extend([questionary.Choice(project, project) for project in projects])

        # Prompt for project
        selectedproject = questionary.select(
            "Select project to filter by:",
            choices=projectchoices,
            style=style
        ).ask()

        # Get tasks for selected project
        if selectedproject:
            tasks = tasklist(project=selectedproject, includedeleted=False)
            printtasktable(tasks, f"Project: {selectedproject}")
        else:
            # Show all projects with their tasks
            for project in projects:
                projecttasks = tasklist(project=project, includedeleted=False)
                if projecttasks:
                    printtasktable(projecttasks, f"Project: {project}")

    elif filtertype == "tags":
        # Get all tags from tasks
        alltasks = tasklist(includeall=True, includedeleted=False)
        alltags = []
        for task in alltasks:
            if task.tags:
                alltags.extend(task.tags)

        tags = sorted(list(set(alltags)))

        if not tags:
            console.print("[yellow]No tags found in tasks.[/]")
            return

        # Prompt for tag selection (allow multiple)
        selectedtags = questionary.checkbox(
            "Select tags to filter by (space to select, enter to confirm):",
            choices=tags,
            style=style
        ).ask()

        if selectedtags:
            tasks = tasklist(tags=selectedtags)
            tag_list = ", ".join(selectedtags)
            printtasktable(tasks, f"Tags: {tag_list}")
        else:
            console.print("[yellow]No tags selected.[/]")

    elif filtertype == "priority":
        # Priority options
        prioritychoices = [
            questionary.Choice("High (H)", "H"),
            questionary.Choice("Medium (M)", "M"),
            questionary.Choice("Low (L)", "L"),
            questionary.Choice("No Priority", "")
        ]

        # Prompt for priority
        selectedpriority = questionary.select(
            "Select priority to filter by:",
            choices=prioritychoices,
            style=style
        ).ask()

        # Get tasks for selected priority
        if selectedpriority is not None:  # Include empty string
            tasks = tasklist(priority=selectedpriority)
            priority_display = selectedpriority if selectedpriority else "No Priority"
            printtasktable(tasks, f"Priority: {priority_display}")

    elif filtertype == "status":
        # Status options
        statuschoices = [
            questionary.Choice("Pending", "pending"),
            questionary.Choice("Completed", "completed"),
            questionary.Choice("Waiting", "waiting"),
            questionary.Choice("Deleted", "deleted")
        ]

        # Prompt for status
        selectedstatus = questionary.select(
            "Select status to filter by:",
            choices=statuschoices,
            style=style
        ).ask()

        # Get tasks for selected status
        if selectedstatus:
            tasks = tasklist(status=selectedstatus)
            printtasktable(tasks, f"Status: {selectedstatus.capitalize()}")

    elif filtertype == "advanced":
        # Advanced filtering - allow custom filter text
        customfilter = questionary.text(
            "Enter custom filter (TaskWarrior syntax):",
            style=style
        ).ask()

        if customfilter:
            # Split into args
            filterargs = customfilter.split()
            if filterargs:
                tasks = tasklist(filterargs=filterargs, includeall=True)
                printtasktable(tasks, f"Custom Filter: {customfilter}")
        else:
            console.print("[yellow]No filter provided.[/]")

def applyquickfilter(filterchoice):
    """Apply a quick filter selection."""
    # Get saved filters
    savedfilters = getconfig("filters", "savedfilters") or {}

    try:
        if filterchoice == "pending":
            tasks = tasklist()
            printtasktable(tasks, "Pending Tasks")
        elif filterchoice == "today":
            listtoday()
        elif filterchoice == "tomorrow":
            # List tasks due tomorrow
            tomorrow = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
            tasks = tasklist(filterargs=[f"due:{tomorrow}"])
            printtasktable(tasks, "Tomorrow's Tasks")
        elif filterchoice == "week":
            listweek()
        elif filterchoice == "overdue":
            listoverdue()
        elif filterchoice == "completed":
            tasks = tasklist(status="completed")
            printtasktable(tasks, "Completed Tasks")
        elif filterchoice == "all":
            # Get all tasks except deleted ones
            tasks = tasklist(includeall=True, includedeleted=False)
            printtasktable(tasks, "All Active Tasks")
        elif filterchoice == "all-with-deleted":
            # Get all tasks including deleted ones
            tasks = tasklist(includeall=True, includedeleted=True)
            printtasktable(tasks, "All Tasks (Including Deleted)")
        elif filterchoice in savedfilters:
            try:
                tasks = tasklist(filterargs=savedfilters[filterchoice])
                printtasktable(tasks, f"Filter: {filterchoice}")
            except Exception as e:
                # Fallback to all tasks if the saved filter fails
                log.error(f"Error applying saved filter '{filterchoice}': {str(e)}")
                console.print(f"[yellow]Error applying filter '{filterchoice}'. Showing all tasks instead.[/]")
                tasks = tasklist(includeall=True, includedeleted=False)
                printtasktable(tasks, "All Active Tasks")
    except Exception as e:
        log.error(f"Error listing tasks: {str(e)}")
        console.print("[red]An error occurred while listing tasks.[/]")
        console.print(f"[red]{str(e)}[/]")


@app.command("project")
def listproject(
    project: Optional[str] = typer.Argument(
        None, help="Project name to filter by"
    )
):
    """List tasks for a specific project."""
    if not project:
        # Interactive project selection
        alltasks = tasklist(includeall=True, includedeleted=False)
        projects = sorted(list(set([task.project for task in alltasks if task.project])))

        if not projects:
            console.print("[yellow]No projects found in tasks.[/]")
            return

        # Prompt for project
        style = questionary.Style.from_dict(getstyle())
        selectedproject = questionary.select(
            "Select project to filter by:",
            choices=projects,
            style=style
        ).ask()

        if selectedproject:
            project = selectedproject
        else:
            return

    # Get tasks for the selected project (only include active tasks)
    tasks = tasklist(project=project, includedeleted=False)

    # Additional safety check - make sure we only show matching tasks
    tasks = [task for task in tasks if task.project == project]

    printtasktable(tasks, f"Project: {project}")

@app.command("tag")
def listtag(
    tag: Optional[str] = typer.Argument(
        None, help="Tag to filter by"
    )
):
    """List tasks with a specific tag."""
    if not tag:
        # Interactive tag selection
        alltasks = tasklist(includeall=True, includedeleted=False)
        alltags = []
        for task in alltasks:
            if task.tags:
                alltags.extend(task.tags)

        tags = sorted(list(set(alltags)))

        if not tags:
            console.print("[yellow]No tags found in tasks.[/]")
            return

        # Prompt for tag
        style = questionary.Style.from_dict(getstyle())
        selectedtag = questionary.select(
            "Select tag to filter by:",
            choices=tags,
            style=style
        ).ask()

        if selectedtag:
            tag = selectedtag
        else:
            return

    # Get tasks with the selected tag
    tasks = tasklist(tags=[tag], includedeleted=False)
    printtasktable(tasks, f"Tag: {tag}")


@app.command("tomorrow")
def listtomorrow():
    """List tasks due tomorrow."""
    tomorrow = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    tasks = tasklist(filterargs=[f"due:{tomorrow}"])
    printtasktable(tasks, "Tomorrow's Tasks")

@app.command("month")
def listmonth():
    """List tasks due this month."""
    tasks = tasklist(filterargs=["due:month"])
    printtasktable(tasks, "This Month's Tasks")

@app.command("upcoming")
def listupcoming(
    days: int = typer.Argument(
        14, help="Number of days to look ahead"
    )
):
    """List upcoming tasks for the specified number of days."""
    tasks = tasklist(filterargs=[f"due.before:now+{days}days", "due.after:now"])
    printtasktable(tasks, f"Upcoming Tasks ({days} days)")

@app.command("due")
def listdue(
    date: str = typer.Argument(
        ..., help="Due date (YYYY-MM-DD or relative like 'today', 'tomorrow')"
    )
):
    """List tasks due on a specific date."""
    tasks = tasklist(filterargs=[f"due:{date}"])
    printtasktable(tasks, f"Tasks Due: {date}")
