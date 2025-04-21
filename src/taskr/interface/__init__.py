# ~/taskr/src/taskr/interface/__init__.py
"""
TaskWarrior interface package.

This package provides functionality for interacting with TaskWarrior.
"""

from .command import (
    execute,
    getcommandpath,
    buildcommand,
    commandexists
)
from .task import (
    Task,
    parsetask,
    formattask,
    tasklist,
    gettask,
    addtask,
    modifytask,
    completetask,
    deletetask
)
from .export import (
    exporttasks,
    importtasks,
    backuptasks
)

__all__ = [
    # Command execution
    'execute',
    'getcommandpath',
    'buildcommand',
    'commandexists',

    # Task handling
    'Task',
    'parsetask',
    'formattask',
    'tasklist',
    'gettask',
    'addtask',
    'modifytask',
    'completetask',
    'deletetask',

    # Import/export
    'exporttasks',
    'importtasks',
    'backuptasks'
]
