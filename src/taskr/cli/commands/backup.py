# ~/taskr/src/taskr/cli/commands/backup.py
"""
Backup command.

This module provides the command for backing up TaskWarrior data.
"""

import typer
import os
from datetime import datetime
from typing import Optional

from taskr.interface import backuptasks, exporttasks
from taskr.cli.common import console

# Create command app
app = typer.Typer()


@app.callback(invoke_without_command=True)
def backupcallback(
    outputdir: Optional[str] = typer.Argument(
        None, help="Output directory for backup"
    )
):
    """
    Backup TaskWarrior data.

    Creates a backup of all TaskWarrior data files.
    """
    backupdir = backuptasks(outputdir)

    if backupdir:
        console.print(f"[bold green]TaskWarrior data backed up to:[/bold green] {backupdir}")
    else:
        console.print("[bold red]Backup failed.[/bold red]")


@app.command("export")
def backupexport(
    outputfile: str = typer.Argument(..., help="Output file path"),
    all: bool = typer.Option(
        False, "--all", "-a", help="Include all tasks (completed and deleted)"
    )
):
    """Export tasks to a JSON file."""
    success = exporttasks(outputfile, all=all)

    if success:
        console.print(f"[bold green]Tasks exported to:[/bold green] {outputfile}")
    else:
        console.print("[bold red]Export failed.[/bold red]")


@app.command("all")
def backupall(
    outputdir: Optional[str] = typer.Option(
        None, "--dir", "-d", help="Output directory"
    )
):
    """Backup both TaskWarrior data and export tasks to JSON."""
    # Create backup directory
    if not outputdir:
        outputdir = os.path.join(
            os.path.expanduser("~/.taskr/backups"),
            datetime.now().strftime("%Y%m%d-%H%M%S")
        )

    os.makedirs(outputdir, exist_ok=True)

    # Backup data
    backupdir = backuptasks(outputdir)

    if not backupdir:
        console.print("[bold red]Data backup failed.[/bold red]")
        return

    # Export tasks
    exportfile = os.path.join(outputdir, "tasks.json")
    success = exporttasks(exportfile, all=True)

    if not success:
        console.print("[bold red]Task export failed.[/bold red]")
        return

    console.print(f"[bold green]Full backup completed:[/bold green] {outputdir}")
    console.print(f"  - Data files: {backupdir}")
    console.print(f"  - Tasks export: {exportfile}")
