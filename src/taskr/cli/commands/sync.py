# ~/taskr/src/taskr/cli/commands/sync.py
"""
Sync command.

This module provides commands for synchronizing tasks with external services.
"""

import typer
import questionary
from typing import Optional, List

from taskr.logs import log
from taskr.cli.common import console, getstyle, confirmaction
from taskr.config.syncs import gettargetconfig, updatetargetconfig
from taskr.sync.taskd import TaskdSync
from taskr.sync.reminders.manager import ReminderSync

# Create command app
app = typer.Typer()


@app.callback(invoke_without_command=True)
def synccallback():
    """
    Synchronize tasks with external services.

    Use subcommands to sync with specific targets.
    """
    console.print("[bold cyan]Available sync targets:[/bold cyan]")
    console.print("  taskd     - TaskWarrior Server sync")
    console.print("  reminders - Apple Reminders sync")
    console.print("\nUse [bold]taskr sync <target>[/bold] to sync with a specific target.")


@app.command("taskd")
def synctaskd(
    export: bool = typer.Option(
        True, "--export/--no-export", help="Export tasks to TaskServer"
    ),
    auto: bool = typer.Option(
        False, "--auto/--no-auto", help="Set auto-sync for future exports"
    )
):
    """Sync with TaskWarrior Server (taskd)."""
    # Update configuration if auto flag provided
    if auto:
        updatetargetconfig("taskd", exportsauto=auto)
        status = "enabled" if auto else "disabled"
        console.print(f"[bold green]Auto-sync with taskd {status}.[/bold green]")

    if export:
        taskd = TaskdSync()
        console.print("[bold cyan]Syncing with TaskWarrior Server...[/bold cyan]")
        changes = taskd.exports()
        console.print(f"[bold green]Sync completed with {changes} changes.[/bold green]")


@app.command("reminders")
def syncreminders(
    export: bool = typer.Option(
        True, "--export/--no-export", help="Export tasks to Reminders"
    ),
    imports: bool = typer.Option(
        True, "--import/--no-import", help="Import reminders as tasks"
    ),
    autoexport: bool = typer.Option(
        None, "--auto-export/--no-auto-export", help="Set auto-export for future syncs"
    ),
    autoimport: bool = typer.Option(
        None, "--auto-import/--no-auto-import", help="Set auto-import for future syncs"
    ),
    list: Optional[str] = typer.Option(
        None, "--list", "-l", help="Reminders list to sync with"
    ),
    interactive: bool = typer.Option(
        True, "--interactive/--no-interactive", "-i", help="Use interactive mode"
    )
):
    """Sync with Apple Reminders."""
    if interactive:
        syncremindersinteractive()
    else:
        # Update configuration if auto flags provided
        if autoexport is not None:
            updatetargetconfig("reminders", exportsauto=autoexport)
            status = "enabled" if autoexport else "disabled"
            console.print(f"[bold green]Auto-export to Reminders {status}.[/bold green]")

        if autoimport is not None:
            updatetargetconfig("reminders", importsauto=autoimport)
            status = "enabled" if autoimport else "disabled"
            console.print(f"[bold green]Auto-import from Reminders {status}.[/bold green]")

        # Perform sync operations
        reminders = ReminderSync(list)

        if imports:
            console.print("[bold cyan]Importing from Reminders...[/bold cyan]")
            changes = reminders.imports()
            console.print(f"[bold green]Import completed with {changes} tasks created/updated.[/bold green]")

        if export:
            console.print("[bold cyan]Exporting to Reminders...[/bold cyan]")
            changes = reminders.exports()
            console.print(f"[bold green]Export completed with {changes} reminders created/updated.[/bold green]")


def syncremindersinteractive():
    """Sync with Apple Reminders using interactive prompts."""
    # Set up questionary style
    style = questionary.Style.from_dict(getstyle())

    # Get available Reminders lists
    from taskr.sync.reminders.osa import osascript
    reminderlists = osascript.getlists()

    # Add option to create a new list
    if reminderlists:
        reminderlists.append("Create a new list")
    else:
        reminderlists = ["Create a new list"]

    # Prompt for list selection
    selectedlist = questionary.select(
        "Select Reminders list to sync with:",
        choices=reminderlists,
        style=style
    ).ask()

    if not selectedlist:
        return

    # Handle creating a new list
    if selectedlist == "Create a new list":
        newlist = questionary.text(
            "Enter name for new Reminders list:",
            style=style
        ).ask()

        if not newlist:
            console.print("[yellow]No list name provided. Cancelling sync.[/yellow]")
            return

        success = osascript.createlist(newlist)
        if not success:
            console.print(f"[bold red]Failed to create list '{newlist}'.[/bold red]")
            return

        selectedlist = newlist
        console.print(f"[bold green]Created new Reminders list: {newlist}[/bold green]")

    # Prompt for sync operations
    operations = questionary.checkbox(
        "Select sync operations:",
        choices=[
            questionary.Choice("Import reminders as tasks", "import"),
            questionary.Choice("Export tasks to reminders", "export")
        ],
        style=style
    ).ask()

    if not operations:
        console.print("[yellow]No operations selected. Cancelling sync.[/yellow]")
        return

    # Initialize ReminderSync with selected list
    reminders = ReminderSync(selectedlist)

    # Perform selected operations
    if "import" in operations:
        console.print(f"[bold cyan]Importing from Reminders list '{selectedlist}'...[/bold cyan]")
        changes = reminders.imports()
        console.print(f"[bold green]Import completed with {changes} tasks created/updated.[/bold green]")

    if "export" in operations:
        console.print(f"[bold cyan]Exporting to Reminders list '{selectedlist}'...[/bold cyan]")
        changes = reminders.exports()
        console.print(f"[bold green]Export completed with {changes} reminders created/updated.[/bold green]")

    # Prompt for auto-sync settings
    if questionary.confirm(
        "Configure auto-sync settings?",
        default=False,
        style=style
    ).ask():
        # Auto-export
        autoexport = questionary.confirm(
            "Enable auto-export to Reminders?",
            default=False,
            style=style
        ).ask()

        # Auto-import
        autoimport = questionary.confirm(
            "Enable auto-import from Reminders?",
            default=False,
            style=style
        ).ask()

        # Save settings
        updatetargetconfig("reminders", exportsauto=autoexport, importsauto=autoimport)

        # Save list preference
        remindersconfig = gettargetconfig("reminders")
        if remindersconfig:
            options = remindersconfig.options
            options["defaultlist"] = selectedlist
            updatetargetconfig("reminders", options=options)

        console.print("[bold green]Auto-sync settings updated.[/bold green]")


@app.command("status")
def syncstatus():
    """Show the current sync configuration status."""
    # Get sync configs
    taskdconfig = gettargetconfig("taskd")
    remindersconfig = gettargetconfig("reminders")

    # Display status
    console.print("[bold cyan]Sync Status:[/bold cyan]")

    # TaskD status
    console.print("\n[bold]TaskWarrior Server (taskd):[/bold]")
    if taskdconfig:
        console.print(f"  Export enabled: {taskdconfig.exportsenabled}")
        console.print(f"  Auto-export: {taskdconfig.exportsauto}")
    else:
        console.print("  [yellow]Not configured[/yellow]")

    # Reminders status
    console.print("\n[bold]Apple Reminders:[/bold]")
    if remindersconfig:
        console.print(f"  Export enabled: {remindersconfig.exportsenabled}")
        console.print(f"  Auto-export: {remindersconfig.exportsauto}")
        console.print(f"  Import enabled: {remindersconfig.importsenabled}")
        console.print(f"  Auto-import: {remindersconfig.importsauto}")
        console.print(f"  Default list: {remindersconfig.options.get('defaultlist', 'Not set')}")
    else:
        console.print("  [yellow]Not configured[/yellow]")


@app.command("auto")
def syncauto():
    """Run all enabled auto-sync operations."""
    # Get sync configs
    taskdconfig = gettargetconfig("taskd")
    remindersconfig = gettargetconfig("reminders")

    # Track sync operations
    syncsperformed = 0

    # TaskD auto-sync
    if taskdconfig and taskdconfig.exportsenabled and taskdconfig.exportsauto:
        console.print("[bold cyan]Auto-syncing with TaskWarrior Server...[/bold cyan]")
        taskd = TaskdSync()
        changes = taskd.exports()
        console.print(f"[bold green]TaskD sync completed with {changes} changes.[/bold green]")
        syncsperformed += 1

    # Reminders auto-sync
    if remindersconfig:
        defaultlist = remindersconfig.options.get("defaultlist")
        reminders = ReminderSync(defaultlist)

        # Auto-import
        if remindersconfig.importsenabled and remindersconfig.importsauto:
            console.print(f"[bold cyan]Auto-importing from Reminders{' list \'' + defaultlist + '\'' if defaultlist else ''}...[/bold cyan]")
            changes = reminders.imports()
            console.print(f"[bold green]Reminders import completed with {changes} tasks created/updated.[/bold green]")
            syncsperformed += 1

        # Auto-export
        if remindersconfig.exportsenabled and remindersconfig.exportsauto:
            console.print(f"[bold cyan]Auto-exporting to Reminders{' list \'' + defaultlist + '\'' if defaultlist else ''}...[/bold cyan]")
            changes = reminders.exports()
            console.print(f"[bold green]Reminders export completed with {changes} reminders created/updated.[/bold green]")
            syncsperformed += 1

    # Summary
    if syncsperformed == 0:
        console.print("[yellow]No auto-sync operations enabled. Use 'taskr sync status' to view current settings.[/yellow]")
    else:
        console.print(f"[bold green]Auto-sync completed with {syncsperformed} operations.[/bold green]")


@app.command("enable")
def syncenable(
    target: str = typer.Argument(..., help="Sync target to enable"),
    imports: bool = typer.Option(
        True, "--import/--no-import", help="Enable/disable imports"
    ),
    export: bool = typer.Option(
        True, "--export/--no-export", help="Enable/disable exports"
    ),
    autoimport: bool = typer.Option(
        False, "--auto-import/--no-auto-import", help="Enable/disable auto-import"
    ),
    autoexport: bool = typer.Option(
        False, "--auto-export/--no-auto-export", help="Enable/disable auto-export"
    )
):
    """Enable or disable sync operations for a target."""
    # Normalize target name
    target = target.lower()

    # Validate target
    if target not in ["taskd", "reminders"]:
        console.print(f"[bold red]Unknown sync target: {target}[/bold red]")
        console.print("Valid targets are: taskd, reminders")
        return

    # Update configuration
    success = updatetargetconfig(
        target,
        importsenabled=imports,
        exportsenabled=export,
        importsauto=autoimport,
        exportsauto=autoexport
    )

    if success:
        console.print(f"[bold green]Sync settings for {target} updated:[/bold green]")
        console.print(f"  Import enabled: {imports}")
        console.print(f"  Export enabled: {export}")
        console.print(f"  Auto-import: {autoimport}")
        console.print(f"  Auto-export: {autoexport}")
    else:
        console.print(f"[bold red]Failed to update sync settings for {target}.[/bold red]")
