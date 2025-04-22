# ~/taskr/src/taskr/interface/command.py
"""
TaskWarrior command execution module.

This module provides functions for executing TaskWarrior commands.
"""
import os, shlex, typing as t, subprocess as sub, traceback as tb
from pathlib import Path

from taskr.logs import log
from taskr.config import getconfig


def getcommandpath() -> str:
    """
    Get the path to the TaskWarrior command.

    Returns:
        Path to the TaskWarrior command.
    """
    return getconfig("taskwarrior", "command")


def commandexists() -> bool:
    """
    Check if the TaskWarrior command exists.

    Returns:
        True if the command exists, False otherwise.
    """
    command = getcommandpath()

    try:
        # Try to run 'command --version'
        result = sub.run(
            [command, "--version"],
            stdout=sub.PIPE,
            stderr=sub.PIPE,
            check=False,
            text=True
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def buildcommand(args: t.List[str], raw: bool = False) -> t.List[str]:
    """
    Build a TaskWarrior command.

    Args:
        args: Command arguments.
        raw: Whether to return the raw command string.

    Returns:
        Command list or string.
    """
    command = [getcommandpath()]

    # Add rc options
    datalocation = getconfig("taskwarrior", "data.location")
    if datalocation:
        datalocation = os.path.expanduser(datalocation)
        command.append(f"rc.data.location={datalocation}")

    # Add custom udas if defined
    udas = getconfig("taskwarrior", "udas")
    if udas:
        for udaname, udaconfig in udas.items():
            for k, v in udaconfig.items():
                command.append(f"rc.uda.{udaname}.{k}={v}")

    # Add command arguments
    command.extend(args)

    # Add export options if needed
    if args and args[0] == "export":
        command.append("rc.json.array=on")

    # Return raw command string if requested
    if raw:
        return " ".join(shlex.quote(arg) for arg in command)

    return command


def execute(
    args: t.List[str],
    capture: bool = True,
    check: bool = True,
    allowfail: bool = True,
    inputdata: t.Optional[t.Union[str, bytes]] = None,
    env: t.Optional[t.Dict[str, str]] = None
) -> t.Tuple[int, str, str]:
    """
    Execute a TaskWarrior command.

    Args:
        args: Command arguments.
        capture: Whether to capture command output.
        check: Whether to check for command success.
        allowfail: Whether to allow command failure.
        inputdata: Input data to pass to the command as string or bytes.
        env: Environment variables to set for the command.

    Returns:
        Tuple of (return code, stdout, stderr).
    """
    command = buildcommand(args)

    # Set up environment variables
    cmdenv = os.environ.copy()
    if env:
        cmdenv.update(env)

    # Log command execution
    log.debug(f"executing command: {' '.join(shlex.quote(arg) for arg in command)}")

    try:
        # Process input data - ensure it's bytes
        input_bytes = None
        if inputdata is not None:
            if isinstance(inputdata, str):
                input_bytes = inputdata.encode('utf-8')
            elif isinstance(inputdata, bytes):
                input_bytes = inputdata
            else:
                log.error(f"Invalid input data type: {type(inputdata)}")
                return -1, "", f"Invalid input data type: {type(inputdata)}"

        # Run command with check=False to handle errors ourselves
        result = sub.run(
            command,
            stdout=sub.PIPE if capture else None,
            stderr=sub.PIPE if capture else None,
            input=input_bytes,  # Now properly handled as bytes
            env=cmdenv,
            check=False,
            text=True
        )

        # Get output
        stdout = result.stdout or ""
        stderr = result.stderr or ""

        # Log result if there was an error
        if result.returncode != 0:
            log.debug(f"command failed with code {result.returncode}: {stderr}")

        return result.returncode, stdout, stderr
    except Exception as e:
        # Handle other exceptions
        log.error(f"exception executing command: {str(e)}", tb.format_exc())
        return -1, "", str(e)
