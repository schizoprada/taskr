# ~/taskr/tests/unit/interface/test_export.py
"""Tests for the interface export module."""
import os
import json
import pytest
import shutil
from datetime import datetime

from taskr.interface.export import (
    exporttasks,
    importtasks,
    backuptasks,
    restoretaskwarriorbackup
)


def test_exporttasks(mock_config, mock_taskwarrior_cmd, temp_dir):
    """Test exporttasks function."""
    # Sample task data
    tasks_json = json.dumps([
        {
            'id': 1,
            'description': 'Task 1',
            'status': 'pending'
        },
        {
            'id': 2,
            'description': 'Task 2',
            'status': 'pending',
            'project': 'test'
        }
    ])

    # Set return value for export command
    mock_taskwarrior_cmd.set_return_value('task export status:pending', 0, tasks_json, '')

    # Export tasks
    output_file = os.path.join(temp_dir, 'tasks.json')
    success = exporttasks(output_file)

    # Check result
    assert success is True

    # Check files were restored
    for file in test_files:
        with open(os.path.join(task_dir, file), 'r') as f:
            content = f.read()
        assert content == f'Backup data for {file}'

    # Test restore failure - backup dir doesn't exist
    success = restoretaskwarriorbackup(os.path.join(temp_dir, 'nonexistent'))

    # Check result
    assert success is False

    # Test restore failure - not a directory
    not_dir = os.path.join(temp_dir, 'not_a_dir')
    with open(not_dir, 'w') as f:
        f.write('This is not a directory')

    # Restore from non-directory
    success = restoretaskwarriorbackup(not_dir)

    # Check result
    assert success is False

    # Test restore failure - copy error
    def mock_copy_raises(*args, **kwargs):
        raise OSError("Test error")

    monkeypatch.setattr('shutil.copy2', mock_copy_raises)

    # Restore with copy error
    success = restoretaskwarriorbackup(backup_dir)

    # Check result
    assert success is False


# Helper mock class for datetime
class MockDatetime:
    """Mock class for datetime."""

    @classmethod
    def now(cls):
        class MockNow:
            def strftime(self, fmt):
                return '20250421-000000'
        return MockNow() is True
    assert os.path.exists(output_file)

    # Check exported data
    with open(output_file, 'r') as f:
        exported_data = f.read()

    assert exported_data == tasks_json

    # Test with filters
    mock_taskwarrior_cmd.set_return_value('task export status:pending project:test', 0, json.dumps([tasks_json[1]]), '')

    # Export filtered tasks
    output_file = os.path.join(temp_dir, 'filtered_tasks.json')
    success = exporttasks(output_file, filterargs=['project:test'])

    # Check result
    assert success is True
    assert os.path.exists(output_file)

    # Test export failure
    mock_taskwarrior_cmd.set_return_value('task export status:pending', 1, '', 'Error exporting tasks')

    # Export with error
    output_file = os.path.join(temp_dir, 'failed_export.json')
    success = exporttasks(output_file)

    # Check result
    assert success is False


def test_importtasks(mock_config, mock_taskwarrior_cmd, temp_dir):
    """Test importtasks function."""
    # Create a JSON file with tasks
    tasks_data = [
        {
            'description': 'Imported task 1',
            'status': 'pending'
        },
        {
            'description': 'Imported task 2',
            'status': 'pending',
            'project': 'test'
        }
    ]

    import_file = os.path.join(temp_dir, 'import_tasks.json')
    with open(import_file, 'w') as f:
        json.dump(tasks_data, f)

    # Set return value for import command
    mock_taskwarrior_cmd.set_return_value('task import', 0, 'Imported 2 tasks.', '')

    # Import tasks
    success = importtasks(import_file)

    # Check result
    assert success is True

    # Check input data was passed
    cmd, kwargs = mock_taskwarrior_cmd.commands[0]
    assert 'import' in cmd
    assert 'input' in kwargs
    assert 'Imported task 1' in kwargs['input']

    # Test import with overwrite
    mock_taskwarrior_cmd.set_return_value('task import --overwrite', 0, 'Imported 2 tasks.', '')

    # Import with overwrite
    success = importtasks(import_file, overwrite=True)

    # Check result
    assert success is True

    # Check command included overwrite flag
    cmd, kwargs = mock_taskwarrior_cmd.commands[1]
    assert '--overwrite' in cmd

    # Test import failure - file not found
    success = importtasks(os.path.join(temp_dir, 'nonexistent.json'))

    # Check result
    assert success is False

    # Test import failure - invalid JSON
    invalid_file = os.path.join(temp_dir, 'invalid.json')
    with open(invalid_file, 'w') as f:
        f.write('This is not valid JSON')

    # Import invalid file
    success = importtasks(invalid_file)

    # Check result
    assert success is False

    # Test import failure - not a task array
    not_array_file = os.path.join(temp_dir, 'not_array.json')
    with open(not_array_file, 'w') as f:
        f.write('{"description": "Not an array"}')

    # Import non-array file
    success = importtasks(not_array_file)

    # Check result
    assert success is False

    # Test import command failure
    mock_taskwarrior_cmd.set_return_value('task import', 1, '', 'Error importing tasks')

    # Import with command error
    success = importtasks(import_file)

    # Check result
    assert success is False


def test_backuptasks(mock_config, monkeypatch, temp_dir):
    """Test backuptasks function."""
    # Create TaskWarrior data directory with test files
    from taskr.config import getconfig

    task_dir = os.path.expanduser(getconfig('taskwarrior', 'data.location'))
    os.makedirs(task_dir, exist_ok=True)

    # Create some test files
    test_files = ['pending.data', 'completed.data', 'undo.data']
    for file in test_files:
        with open(os.path.join(task_dir, file), 'w') as f:
            f.write(f'Test data for {file}')

    # Create backup
    backup_dir = os.path.join(temp_dir, 'backup')
    result = backuptasks(backup_dir)

    # Check result
    assert result == backup_dir
    assert os.path.exists(backup_dir)

    # Check files were copied
    for file in test_files:
        assert os.path.exists(os.path.join(backup_dir, file))

        # Check file content
        with open(os.path.join(backup_dir, file), 'r') as f:
            content = f.read()
        assert content == f'Test data for {file}'

    # Test default backup directory
    monkeypatch.setattr('datetime.datetime', MockDatetime)

    # Create backup with default directory
    result = backuptasks()

    # Check result
    assert result is not None
    assert '20250421-000000' in result
    assert os.path.exists(result)

    # Check files were copied
    for file in test_files:
        assert os.path.exists(os.path.join(result, file))

    # Test backup failure
    def mock_copy_raises(*args, **kwargs):
        raise OSError("Test error")

    monkeypatch.setattr('shutil.copy2', mock_copy_raises)

    # Create backup with error
    result = backuptasks(os.path.join(temp_dir, 'failed_backup'))

    # Check result
    assert result is None


def test_restoretaskwarriorbackup(mock_config, monkeypatch, temp_dir):
    """Test restoretaskwarriorbackup function."""
    # Create TaskWarrior data directory with test files
    from taskr.config import getconfig

    task_dir = os.path.expanduser(getconfig('taskwarrior', 'data.location'))
    os.makedirs(task_dir, exist_ok=True)

    # Create some test files
    test_files = ['pending.data', 'completed.data', 'undo.data']
    for file in test_files:
        with open(os.path.join(task_dir, file), 'w') as f:
            f.write(f'Original data for {file}')

    # Create backup directory with different content
    backup_dir = os.path.join(temp_dir, 'backup')
    os.makedirs(backup_dir, exist_ok=True)

    for file in test_files:
        with open(os.path.join(backup_dir, file), 'w') as f:
            f.write(f'Backup data for {file}')

    # Restore from backup
    success = restoretaskwarriorbackup(backup_dir)

    # Check result
    assert success
