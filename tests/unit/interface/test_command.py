# ~/taskr/tests/unit/interface/test_command.py
"""Tests for the interface command module."""
import os
import pytest
import shlex

from taskr.interface.command import (
    getcommandpath,
    commandexists,
    buildcommand,
    execute
)


def test_get_command_path(mock_config):
    """Test getcommandpath function."""
    # Get command path
    command = getcommandpath()

    # Check command
    assert command == 'task'

    # Change command in config
    from taskr.config import setconfig
    setconfig('taskwarrior', 'command', 'custom_task')

    # Check updated command
    command = getcommandpath()
    assert command == 'custom_task'


def test_command_exists(mock_config, mock_taskwarrior_cmd):
    """Test commandexists function."""
    # Set return value for command check
    mock_taskwarrior_cmd.set_return_value('task --version', 0, 'task 2.6.0', '')

    # Check command exists
    exists = commandexists()
    assert exists is True

    # Set return value for command not found
    mock_taskwarrior_cmd.set_return_value('task --version', 1, '', 'command not found')

    # Check command doesn't exist
    exists = commandexists()
    assert exists is False


def test_build_command(mock_config):
    """Test buildcommand function."""
    # Build simple command
    cmd = buildcommand(['list'])

    # Check command
    assert isinstance(cmd, list)
    assert cmd[0] == 'task'
    assert 'rc.data.location=' in cmd[1]
    assert cmd[2] == 'list'

    # Set custom command and data location
    from taskr.config import setconfig
    setconfig('taskwarrior', 'command', 'custom_task')
    setconfig('taskwarrior', 'data.location', '/custom/path')

    # Build command with custom settings
    cmd = buildcommand(['list'])

    # Check command
    assert cmd[0] == 'custom_task'
    assert cmd[1] == 'rc.data.location=/custom/path'
    assert cmd[2] == 'list'

    # Build export command
    cmd = buildcommand(['export'])

    # Check export options
    assert 'rc.json.array=on' in cmd

    # Build raw command
    raw_cmd = buildcommand(['list'], raw=True)

    # Check raw command
    assert isinstance(raw_cmd, str)
    assert 'custom_task' in raw_cmd
    assert 'rc.data.location=/custom/path' in raw_cmd
    assert 'list' in raw_cmd


def test_execute_success(mock_config, mock_taskwarrior_cmd):
    """Test execute function with successful command."""
    # Set return value for successful command
    mock_taskwarrior_cmd.set_return_value('task list', 0, 'task output', '')

    # Execute command
    returncode, stdout, stderr = execute(['list'])

    # Check results
    assert returncode == 0
    assert stdout == 'task output'
    assert stderr == ''

    # Check command was called
    cmd, kwargs = mock_taskwarrior_cmd.commands[0]
    assert 'list' in cmd
    assert kwargs.get('check', False) is True
    assert kwargs.get('text', False) is True


def test_execute_failure(mock_config, mock_taskwarrior_cmd):
    """Test execute function with failed command."""
    # Set return value for failed command
    mock_taskwarrior_cmd.set_return_value('task invalid', 1, '', 'task: Invalid command')

    # Execute command with allowfail=True
    returncode, stdout, stderr = execute(['invalid'], allowfail=True)

    # Check results
    assert returncode == 1
    assert stdout == ''
    assert stderr == 'task: Invalid command'

    # Execute command with allowfail=False
    with pytest.raises(Exception):
        execute(['invalid'], allowfail=False)


def test_execute_with_input(mock_config, mock_taskwarrior_cmd):
    """Test execute function with input data."""
    # Set return value for command with input
    mock_taskwarrior_cmd.set_return_value('task import', 0, 'Imported 1 task', '')

    # Execute command with input
    returncode, stdout, stderr = execute(
        ['import'],
        inputdata='{"description":"Test task"}'
    )

    # Check results
    assert returncode == 0
    assert stdout == 'Imported 1 task'

    # Check command was called with input
    cmd, kwargs = mock_taskwarrior_cmd.commands[0]
    assert 'import' in cmd
    assert kwargs.get('input') is not None


def test_execute_with_env(mock_config, mock_taskwarrior_cmd):
    """Test execute function with custom environment."""
    # Set return value
    mock_taskwarrior_cmd.set_return_value('task list', 0, 'task output', '')

    # Execute command with custom environment
    returncode, stdout, stderr = execute(
        ['list'],
        env={'TASKRC': '/custom/taskrc'}
    )

    # Check command was called with environment
    cmd, kwargs = mock_taskwarrior_cmd.commands[0]
    assert 'list' in cmd
    assert 'env' in kwargs
    assert kwargs['env'].get('TASKRC') == '/custom/taskrc'
