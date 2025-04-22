# ~/taskr/src/taskr/interface/task.py
"""
TaskWarrior task handling module.

This module provides functions for handling TaskWarrior tasks.
"""

import json
import typing as t
import datetime
from dataclasses import dataclass, field, asdict

from taskr.logs import log
from taskr.interface.command import execute, buildcommand


@dataclass
class Task:
    """TaskWarrior task data class."""

    # Core task attributes
    id: t.Optional[int] = None
    uuid: t.Optional[str] = None
    description: str = ""
    status: str = "pending"

    # Dates
    entry: t.Optional[str] = None
    start: t.Optional[str] = None
    end: t.Optional[str] = None
    due: t.Optional[str] = None
    scheduled: t.Optional[str] = None
    until: t.Optional[str] = None
    wait: t.Optional[str] = None
    modified: t.Optional[str] = None

    # Task metadata
    priority: t.Optional[str] = None
    project: t.Optional[str] = None
    tags: t.List[str] = field(default_factory=list)
    annotations: t.List[t.Dict[str, str]] = field(default_factory=list)
    depends: t.Optional[str] = None

    # Additional fields
    urgency: t.Optional[float] = None
    udas: t.Dict[str, t.Any] = field(default_factory=dict)

    def asdict(self) -> t.Dict[str, t.Any]:
        """
        Convert task to dictionary.

        Returns:
            Dictionary representation of the task.
        """
        result = {}

        # Convert dataclass to dict
        data = asdict(self)

        # Filter out None values and empty lists
        for k, v in data.items():
            if v is not None and not (isinstance(v, list) and len(v) == 0):
                result[k] = v

        # Add UDAs
        for k, v in self.udas.items():
            if v is not None:
                result[k] = v

        return result

    def asjson(self) -> str:
        """
        Convert task to JSON.

        Returns:
            JSON representation of the task.
        """
        return json.dumps(self.asdict())


def parsetask(taskdata: t.Dict[str, t.Any]) -> Task:
    """
    Parse task data into a Task object.

    Args:
        taskdata: Task data from TaskWarrior.

    Returns:
        Task object.
    """
    # Copy task data
    data = taskdata.copy()

    # Extract core fields
    core_fields = {
        field.name for field in Task.__dataclass_fields__.values()
        if field.name != "udas"
    }

    # Extract UDAs (fields not in core fields)
    udas = {}
    for k, v in list(data.items()):
        if k not in core_fields:
            udas[k] = data.pop(k)

    # Create task
    task = Task(**data)
    task.udas = udas

    return task


def formattask(task: Task) -> t.Dict[str, t.Any]:
    """
    Format task data for TaskWarrior.

    Args:
        task: Task object.

    Returns:
        Formatted task data.
    """
    # Convert task to dictionary
    data = task.asdict()

    # Process UDAs
    if "udas" in data:
        udas = data.pop("udas")
        for k, v in udas.items():
            data[k] = v

    return data


def tasklist(
    filterargs: t.Optional[t.List[str]] = None,
    status: t.Optional[str] = None,
    project: t.Optional[str] = None,
    tags: t.Optional[t.List[str]] = None,
    priority: t.Optional[str] = None,
    includeall: bool = False,
    includedeleted: bool = False  # Using this parameter name instead of includedeleted for consistency
) -> t.List[Task]:
    """
    Get a list of tasks.

    Args:
        filterargs: Additional filter arguments.
        status: Task status filter.
        project: Project filter.
        tags: Tags filter.
        priority: Priority filter.
        includeall: Whether to include all tasks.
        includedeleted: Whether to include deleted tasks.

    Returns:
        List of tasks.
    """
    # Build command args
    # First add all filters, THEN add the export command
    args = []

    # Apply status filter
    if status:
        args.append(f"status:{status}")
    elif not includeall:
        args.append("status:pending")
    # No status filter if 'includeall=True' to get everything, we'll filter deleted tasks later

    # Add other filters
    if filterargs:
        args.extend(filterargs)

    if project:
        args.append(f"project:{project}")

    if tags:
        for tag in tags:
            args.append(f"+{tag}")

    if priority:
        args.append(f"priority:{priority}")

    # Add export command AFTER filters
    args.append("export")

    # Execute command with allowfail=True to handle non-zero exits gracefully
    returncode, stdout, stderr = execute(args, allowfail=True)

    if returncode != 0:
        # Log the error but don't raise an exception
        log.error(f"Error retrieving task list: {stderr}")
        # Check if this is a "no matching tasks" type of error
        if "Unable to find report" in stderr or "No matches" in stderr:
            log.info("No tasks match the specified filters.")
        return []

    # Parse tasks
    try:
        tasksdata = json.loads(stdout) if stdout.strip() else []
        alltasks = [parsetask(taskdata) for taskdata in tasksdata]

        # Post-process filtered tasks
        filteredtasks = []

        for task in alltasks:
            # Skip deleted tasks if not includedeleted
            if not includedeleted and task.status == "deleted":
                continue

            # Apply project filter if specified
            if project and task.project != project:
                continue

            # Apply tags filter if specified
            if tags and (not task.tags or not all(tag in task.tags for tag in tags)):
                continue

            # Apply priority filter if specified
            if priority is not None and task.priority != priority:
                continue

            # Include this task
            filteredtasks.append(task)

        return filteredtasks
    except json.JSONDecodeError:
        log.error(f"Error parsing task list JSON: {stdout}")
        return []


def gettask(taskid: t.Union[int, str]) -> t.Optional[Task]:
    """
    Get a task by ID or UUID.

    Args:
        taskid: Task ID or UUID.

    Returns:
        Task object or None if task not found.
    """
    # First, try to get all tasks and filter by ID
    try:
        alltasks = tasklist(includeall=True)

        # Find the task with the matching ID
        for task in alltasks:
            if str(task.id) == str(taskid):
                return task

        # If we get here, task was not found in the full list
        log.debug(f"Task with ID {taskid} not found in full task list")
    except Exception as e:
        log.error(f"Error searching for task {taskid} in task list: {str(e)}")

    # As a fallback, try the traditional export approach
    try:
        # Build command args
        args = ["export", str(taskid)]

        # Execute command with allowfail=True
        returncode, stdout, stderr = execute(args, allowfail=True)

        if returncode != 0:
            log.error(f"error retrieving task {taskid}: {stderr}")
            return None

        # Parse task
        try:
            tasksdata = json.loads(stdout)
            if not tasksdata:
                return None

            return parsetask(tasksdata[0])
        except (json.JSONDecodeError, IndexError):
            log.error(f"error parsing task {taskid}: {stdout}")
            return None
    except Exception as e:
        log.error(f"Exception in fallback task lookup: {str(e)}")
        return None


def addtask(
    description: str,
    project: t.Optional[str] = None,
    priority: t.Optional[str] = None,
    tags: t.Optional[t.List[str]] = None,
    due: t.Optional[str] = None,
    scheduled: t.Optional[str] = None,
    wait: t.Optional[str] = None,
    depends: t.Optional[str] = None,
    annotations: t.Optional[t.List[str]] = None,
    udas: t.Optional[t.Dict[str, t.Any]] = None
) -> t.Optional[Task]:
    """
    Add a new task.

    Args:
        description: Task description.
        project: Project name.
        priority: Task priority.
        tags: Task tags.
        due: Due date.
        scheduled: Scheduled date.
        wait: Wait date.
        depends: Dependencies.
        annotations: Annotations.
        udas: User-defined attributes.

    Returns:
        Added task or None if adding failed.
    """
    # Build command args
    args = ["add", description]

    # Add attributes
    if project:
        args.append(f"project:{project}")

    if priority:
        args.append(f"priority:{priority}")

    if tags:
        for tag in tags:
            args.append(f"+{tag}")

    if due:
        args.append(f"due:{due}")

    if scheduled:
        args.append(f"scheduled:{scheduled}")

    if wait:
        args.append(f"wait:{wait}")

    if depends:
        args.append(f"depends:{depends}")

    # Add UDAs
    if udas:
        for k, v in udas.items():
            args.append(f"{k}:{v}")

    # Execute command
    returncode, stdout, stderr = execute(args, allowfail=True)

    if returncode != 0:
        log.error(f"error adding task: {stderr}")
        return None

    # Parse task ID from output using a more robust approach
    try:
        # Output is like "Created task 123." - we need to handle the period at the end
        # Improved parsing to extract the task ID
        import re
        match = re.search(r'Created task (\d+)', stdout)
        if match:
            taskid = int(match.group(1))
            log.debug(f"Successfully parsed task ID: {taskid}")
        else:
            # Fallback approach - try to get the last word and remove any non-digit characters
            last_word = stdout.strip().split()[-1].rstrip('.')
            taskid = int(''.join(filter(str.isdigit, last_word)))
            log.debug(f"Fallback parsing of task ID: {taskid}")

        # Add annotations
        if annotations:
            for annotation in annotations:
                execute([str(taskid), "annotate", annotation])

        # Get the added task
        return gettask(taskid)
    except Exception as e:
        log.error(f"error parsing task ID from output: {stdout}")
        log.error(f"exception details: {str(e)}")

        # Try to return the most recently created task as a fallback
        recent_tasks = tasklist(filterargs=["status:pending", "+LATEST"])
        if recent_tasks and recent_tasks[0].description == description:
            log.debug(f"Using fallback: returning most recently created task with ID {recent_tasks[0].id}")
            return recent_tasks[0]

        return None


def modifytask(
    taskid: t.Union[int, str],
    description: t.Optional[str] = None,
    project: t.Optional[str] = None,
    priority: t.Optional[str] = None,
    tagsadd: t.Optional[t.List[str]] = None,
    tagsremove: t.Optional[t.List[str]] = None,
    due: t.Optional[str] = None,
    scheduled: t.Optional[str] = None,
    wait: t.Optional[str] = None,
    depends: t.Optional[str] = None,
    annotations: t.Optional[t.List[str]] = None,
    udas: t.Optional[t.Dict[str, t.Any]] = None
) -> t.Optional[Task]:
    """
    Modify a task.

    Args:
        taskid: Task ID or UUID.
        description: New task description.
        project: New project name.
        priority: New task priority.
        tagsadd: Tags to add.
        tagsremove: Tags to remove.
        due: New due date.
        scheduled: New scheduled date.
        wait: New wait date.
        depends: New dependencies.
        annotations: Annotations to add.
        udas: User-defined attributes to set.

    Returns:
        Modified task or None if modification failed.
    """
    # Build command args
    args = [str(taskid), "modify"]

    # Add attributes
    if description:
        args.append(f"description:{description}")

    if project:
        args.append(f"project:{project}")

    if priority:
        args.append(f"priority:{priority}")

    if tagsadd:
        for tag in tagsadd:
            args.append(f"+{tag}")

    if tagsremove:
        for tag in tagsremove:
            args.append(f"-{tag}")

    if due:
        args.append(f"due:{due}")
    elif due == "":
        args.append("due:")

    if scheduled:
        args.append(f"scheduled:{scheduled}")
    elif scheduled == "":
        args.append("scheduled:")

    if wait:
        args.append(f"wait:{wait}")
    elif wait == "":
        args.append("wait:")

    if depends:
        args.append(f"depends:{depends}")
    elif depends == "":
        args.append("depends:")

    # Add UDAs
    if udas:
        for k, v in udas.items():
            if v:
                args.append(f"{k}:{v}")
            else:
                args.append(f"{k}:")

    # Execute command if there are modifications
    if len(args) > 2:
        returncode, stdout, stderr = execute(args)

        if returncode != 0:
            log.error(f"error modifying task {taskid}: {stderr}")
            return None

    # Add annotations
    if annotations:
        for annotation in annotations:
            execute([str(taskid), "annotate", annotation])

    # Get the modified task
    return gettask(taskid)


def completetask(taskid: t.Union[int, str]) -> bool:
    """
    Complete a task.

    Args:
        taskid: Task ID or UUID.

    Returns:
        True if task was completed, False otherwise.
    """
    # Build command args
    args = [str(taskid), "done"]

    # Execute command
    returncode, stdout, stderr = execute(args, allowfail=True)

    if returncode != 0:
        log.error(f"error completing task {taskid}: {stderr}")
        return False

    return True


def deletetask(taskid: t.Union[int, str]) -> bool:
    """
    Delete a task.

    Args:
        taskid: Task ID or UUID.

    Returns:
        True if task was deleted, False otherwise.
    """
    # Try to delete with --yes flag to avoid interactive confirmation
    try:
        args = [str(taskid), "delete"]
        returncode, stdout, stderr = execute(args, allowfail=True, inputdata=None)

        if returncode == 0 or "Deleted 1 task" in stdout:
            return True

        # If that failed, try using a different approach
        import subprocess, os
        from taskr.config import getconfig
        taskwarrior_cmd = getconfig("taskwarrior", "command")
        datalocation = getconfig("taskwarrior", "data.location")

        # Use the echo command to provide a single "yes" and pipe it to TaskWarrior
        cmd = f"{taskwarrior_cmd} rc.data.location={datalocation} {taskid} delete"
        shell_cmd = f"echo yes | {cmd}"

        try:
            # Set a timeout to prevent hanging
            subprocess.check_call(shell_cmd, shell=True, timeout=5)
            return True
        except subprocess.TimeoutExpired:
            log.error(f"Shell command timed out. Task may or may not be deleted.")
            return False
        except Exception as e:
            log.error(f"Shell deletion failed: {str(e)}")
            return False

    except Exception as e:
        log.error(f"Error deleting task {taskid}: {str(e)}")
        return False
