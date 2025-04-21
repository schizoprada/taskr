# ~/taskr/src/taskr/cli/commands/restore.py
"""
Restore command.

This module provides the command for restoring TaskWarrior data.
"""

import typer
import os
from typing import Optional
import questionary

from taskr.interface import restoretaskwarriorbackup, importtasks
from taskr.cli.common import console, getstyle, confirmaction

# Create command app
app = typer.Typer()


@app.callback(invoke_without_command=True)
def restorecallback(
    backupdir: Optional[str] = typer.Argument(
        None, help="Backup directory to restore from"
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Force restore without confirmation"
    )
):
    """
    Restore TaskWarrior data from backup.

    Restores all TaskWarrior data files from a backup directory.
    """
    if not backupdir:
        # List available backups
        backupbase = os.path.expanduser("~/.taskr/backups")

        if not os.path.exists(backupbase):
            console.print("[bold red]No backups found.[/bold red]")
            return

        backups = []
        for item in os.listdir(backupbase):
            item_path = os.path.join(backupbase, item)
            if os.path.isdir(item_path):
                backups.append(item)

        if not backups:
            console.print("[bold red]No backups found.[/bold red]")
            return

        # Sort backups by name (newest first)
        backups.sort(reverse=True)

        # Prompt for backup selection
        style = questionary.Style.from_dict(getstyle())

        selected = questionary.select(
            "Select backup to restore:",
            choices=backups,
            style=style
        ).ask()

        if not selected:
            return

        backupdir = os.path.join(backupbase, selected)

    # Confirm restore
    if not force:
        confirmed = confirmaction(
            f"[bold yellow]Restore TaskWarrior data from {backupdir}?[/bold yellow]\n"
            "This will overwrite your current TaskWarrior data."
        )

        if not confirmed:
            console.print("Restore cancelled.")
            return

    # Restore backup
    success = restoretaskwarriorbackup(backupdir)

    if success:
        console.print(f"[bold green]TaskWarrior data restored from:[/bold green] {backupdir}")
    else:
        console.print("[bold red]Restore failed.[/bold red]")


@app.command("import")
def restoreimport(
    inputfile: str = typer.Argument(..., help="Input file path"),
    overwrite: bool = typer.Option(
        False, "--overwrite", "-o", help="Overwrite existing tasks"
    )
):
    """Import tasks from a JSON file."""
    success = importtasks(inputfile, overwrite=overwrite)

    if success:
        console.print(f"[bold green]Tasks imported from:[/bold green] {inputfile}")
    else:
        console.print("[bold red]Import failed.[/bold red]")
