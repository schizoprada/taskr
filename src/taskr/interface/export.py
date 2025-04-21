# ~/taskr/src/taskr/interface/export.py
"""
TaskWarrior import/export module.

This module provides functions for importing and exporting TaskWarrior tasks.
"""

import os, json, shutil, datetime, typing as t
from pathlib import Path

from taskr.logs import log
from taskr.config import getconfig
from taskr.interface.command import execute, buildcommand


def exporttasks(
    outputfile: str,
    filterargs: t.Optional[t.List[str]] = None,
    all: bool = False
) -> bool:
    """
    Export tasks to a file.

    Args:
        outputfile: Output file path.
        filterargs: Filter arguments.
        all: Whether to include all tasks (including completed and deleted).

    Returns:
        True if export was successful, False otherwise.
    """
    # Build command args
    args = ["export"]

    # Apply filters
    if not all:
        args.append("status:pending")

    if filterargs:
        args.extend(filterargs)

    # Execute command
    returncode, stdout, stderr = execute(args)

    if returncode != 0:
        log.error(f"error exporting tasks: {stderr}")
        return False

    # Write to file
    try:
        with open(outputfile, "w") as f:
            f.write(stdout)
        return True
    except Exception as e:
        log.error(f"error writing export file: {str(e)}")
        return False


def importtasks(
    inputfile: str,
    overwrite: bool = False
) -> bool:
    """
    Import tasks from a file.

    Args:
        inputfile: Input file path.
        overwrite: Whether to overwrite existing tasks.

    Returns:
        True if import was successful, False otherwise.
    """
    # Check if file exists
    if not os.path.exists(inputfile):
        log.error(f"import file not found: {inputfile}")
        return False

    # Read file
    try:
        with open(inputfile, "r") as f:
            data = f.read()
    except Exception as e:
        log.error(f"error reading import file: {str(e)}")
        return False

    # Validate JSON
    try:
        tasks = json.loads(data)
        if not isinstance(tasks, list):
            log.error("import file is not a valid task array")
            return False
    except json.JSONDecodeError:
        log.error("import file is not valid JSON")
        return False

    # Build command args
    args = ["import"]
    if overwrite:
        args.append("--overwrite")

    # Execute command
    returncode, stdout, stderr = execute(args, inputdata=data)

    if returncode != 0:
        log.error(f"error importing tasks: {stderr}")
        return False

    return True


def backuptasks(backupdir: t.Optional[str] = None) -> t.Optional[str]:
    """
    Backup TaskWarrior data.

    Args:
        backupdir: Backup directory. If None, a default directory is used.

    Returns:
        Backup file path if successful, None otherwise.
    """
    # Get TaskWarrior data location
    datalocation = os.path.expanduser(getconfig("taskwarrior", "data.location"))

    # Get or create backup directory
    if backupdir is None:
        backupdir = os.path.join(
            os.path.expanduser("~/.taskr/backups"),
            datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        )

    # Create backup directory
    try:
        os.makedirs(backupdir, exist_ok=True)
    except Exception as e:
        log.error(f"error creating backup directory: {str(e)}")
        return None

    # Copy TaskWarrior data files
    try:
        # Get all files in data directory
        datafiles = [
            f for f in os.listdir(datalocation)
            if os.path.isfile(os.path.join(datalocation, f))
        ]

        # Copy each file
        for file in datafiles:
            src = os.path.join(datalocation, file)
            dst = os.path.join(backupdir, file)
            shutil.copy2(src, dst)

        return backupdir
    except Exception as e:
        log.error(f"error backing up TaskWarrior data: {str(e)}")
        return None


def restoretaskwarriorbackup(backupdir: str) -> bool:
    """
    Restore TaskWarrior data from backup.

    Args:
        backupdir: Backup directory.

    Returns:
        True if restore was successful, False otherwise.
    """
    # Get TaskWarrior data location
    datalocation = os.path.expanduser(getconfig("taskwarrior", "data.location"))

    # Check if backup directory exists
    if not os.path.exists(backupdir) or not os.path.isdir(backupdir):
        log.error(f"backup directory not found: {backupdir}")
        return False

    # Create a backup of current data
    currentbackup = backuptasks()
    if not currentbackup:
        log.error("error creating backup of current data")
        return False

    # Copy backup files to data directory
    try:
        # Get all files in backup directory
        backupfiles = [
            f for f in os.listdir(backupdir)
            if os.path.isfile(os.path.join(backupdir, f))
        ]

        # Copy each file
        for file in backupfiles:
            src = os.path.join(backupdir, file)
            dst = os.path.join(datalocation, file)
            shutil.copy2(src, dst)

        return True
    except Exception as e:
        log.error(f"error restoring TaskWarrior data: {str(e)}")

        # Try to restore from current backup
        try:
            log.info(f"attempting to restore from current backup: {currentbackup}")
            restoretaskwarriorbackup(currentbackup)
        except Exception:
            pass

        return False
