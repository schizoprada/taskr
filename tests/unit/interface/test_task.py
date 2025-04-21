# ~/taskr/tests/unit/interface/test_task.py
"""Tests for the interface task module."""
import json
import pytest
from datetime import datetime

from taskr.interface.task import (
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


def test_task_dataclass():
    """Test Task dataclass."""
    # Create a basic task
    task = Task(
        id=1,
        uuid='00000000-0000-0000-0000-000000000000',
        description='Test task',
        status='pending',
        priority='M',
        project='test',
        tags=['tag1', 'tag2']
    )

    # Check task attributes
    assert task.id == 1
    assert task.uuid == '00000000-0000-0000-0000-000000000000'
    assert task.description == 'Test task'
    assert task.status == 'pending'
    assert task.priority == 'M'
    assert task.project == 'test'
    assert task.tags == ['tag1', 'tag2']

    # Check default values
    assert task.urgency is None
    assert task.udas == {}
    assert task.annotations == []


def test_task_asdict():
    """Test Task.asdict method."""
    # Create a task with various attributes
    task = Task(
        id=1,
        description='Test task',
        priority='H',
        tags=['test'],
        udas={'custom_field': 'value'}
    )

    # Convert to dict
    task_dict = task.asdict()

    # Check dict structure
    assert task_dict['id'] == 1
    assert task_dict['description'] == 'Test task'
    assert task_dict['priority'] == 'H'
    assert task_dict['tags'] == ['test']
    assert task_dict['status'] == 'pending'  # Default value
    assert task_dict['custom_field'] == 'value'  # UDA included

    # Check that None values are excluded
    assert 'due' not in task_dict
    assert 'project' not in task_dict


def test_task_asjson():
    """Test Task.asjson method."""
    # Create a task
    task = Task(
        id=1,
        description='Test task'
    )

    # Convert to JSON
    task_json = task.asjson()

    # Parse JSON
    parsed = json.loads(task_json)

    # Check JSON structure
    assert parsed['id'] == 1
    assert parsed['description'] == 'Test task'
    assert parsed['status'] == 'pending'


def test_parse_task():
    """Test parsetask function."""
    # Create task data
    taskdata = {
        'id': 1,
        'uuid': '00000000-0000-0000-0000-000000000000',
        'description': 'Test task',
        'status': 'pending',
        'priority': 'H',
        'project': 'test',
        'tags': ['tag1', 'tag2'],
        'entry': '20230101T000000Z',
        'urgency': 10.5,
        'custom_field': 'value'  # UDA
    }

    # Parse task
    task = parsetask(taskdata)

    # Check core fields
    assert task.id == 1
    assert task.uuid == '00000000-0000-0000-0000-000000000000'
    assert task.description == 'Test task'
    assert task.status == 'pending'
    assert task.priority == 'H'
    assert task.project == 'test'
    assert task.tags == ['tag1', 'tag2']
    assert task.entry == '20230101T000000Z'
    assert task.urgency == 10.5

    # Check UDAs
    assert 'custom_field' in task.udas
    assert task.udas['custom_field'] == 'value'


def test_format_task():
    """Test formattask function."""
    # Create a task
    task = Task(
        id=1,
        description='Test task',
        priority='H',
        tags=['tag1', 'tag2'],
        udas={'custom_field': 'value'}
    )

    # Format task
    formatted = formattask(task)

    # Check formatted task
    assert formatted['id'] == 1
    assert formatted['description'] == 'Test task'
    assert formatted['priority'] == 'H'
    assert formatted['tags'] == ['tag1', 'tag2']
    assert formatted['status'] == 'pending'

    # Check UDAs are included at top level
    assert 'custom_field' in formatted
    assert formatted['custom_field'] == 'value'
    assert 'udas' not in formatted


def test_tasklist(mock_config, mock_taskwarrior_cmd):
    """Test tasklist function."""
    # Sample task data
    tasks_json = json.dumps([
        {
            'id': 1,
            'description': 'Task 1',
            'status': 'pending',
            'urgency': 5.0
        },
        {
            'id': 2,
            'description': 'Task 2',
            'status': 'pending',
            'project': 'test',
            'urgency': 10.0
        }
    ])

    # Set return value for export command
    mock_taskwarrior_cmd.set_return_value('task export status:pending', 0, tasks_json, '')

    # Get task list
    tasks = tasklist()

    # Check tasks
    assert len(tasks) == 2
    assert tasks[0].id == 1
    assert tasks[0].description == 'Task 1'
    assert tasks[1].id == 2
    assert tasks[1].project == 'test'

    # Test with filters
    mock_taskwarrior_cmd.set_return_value('task export status:pending project:test', 0, '[{"id": 2, "description": "Task 2", "status": "pending", "project": "test"}]', '')

    # Get filtered tasks
    tasks = tasklist(project='test')

    # Check filtered tasks
    assert len(tasks) == 1
    assert tasks[0].id == 2
    assert tasks[0].project == 'test'


def test_gettask(mock_config, mock_taskwarrior_cmd):
    """Test gettask function."""
    # Sample task data
    task_json = json.dumps([
        {
            'id': 1,
            'uuid': '00000000-0000-0000-0000-000000000001',
            'description': 'Test task',
            'status': 'pending',
            'priority': 'H'
        }
    ])

    # Set return value for export command
    mock_taskwarrior_cmd.set_return_value('task export 1', 0, task_json, '')

    # Get task by ID
    task = gettask(1)

    # Check task
    assert task is not None
    assert task.id == 1
    assert task.description == 'Test task'
    assert task.priority == 'H'

    # Test with UUID
    mock_taskwarrior_cmd.set_return_value('task export 00000000-0000-0000-0000-000000000001', 0, task_json, '')

    # Get task by UUID
    task = gettask('00000000-0000-0000-0000-000000000001')

    # Check task
    assert task is not None
    assert task.id == 1

    # Test task not found
    mock_taskwarrior_cmd.set_return_value('task export 999', 0, '[]', '')

    # Get non-existent task
    task = gettask(999)

    # Check task
    assert task is None


def test_addtask(mock_config, mock_taskwarrior_cmd):
    """Test addtask function."""
    # Set return value for add command
    mock_taskwarrior_cmd.set_return_value('task add Test task', 0, 'Created task 1.', '')

    # Set return value for export command (to get the task)
    mock_taskwarrior_cmd.set_return_value('task export 1', 0, json.dumps([
        {
            'id': 1,
            'description': 'Test task',
            'status': 'pending'
        }
    ]), '')

    # Add task
    task = addtask('Test task')

    # Check task
    assert task is not None
    assert task.id == 1
    assert task.description == 'Test task'
    assert task.status == 'pending'

    # Test with additional attributes
    mock_taskwarrior_cmd.set_return_value('task add Complex task project:test priority:H +tag1 +tag2 due:2023-01-01', 0, 'Created task 2.', '')

    # Set return value for export command
    mock_taskwarrior_cmd.set_return_value('task export 2', 0, json.dumps([
        {
            'id': 2,
            'description': 'Complex task',
            'project': 'test',
            'priority': 'H',
            'tags': ['tag1', 'tag2'],
            'due': '20230101T000000Z',
            'status': 'pending'
        }
    ]), '')

    # Add complex task
    task = addtask(
        'Complex task',
        project='test',
        priority='H',
        tags=['tag1', 'tag2'],
        due='2023-01-01'
    )

    # Check task
    assert task is not None
    assert task.id == 2
    assert task.description == 'Complex task'
    assert task.project == 'test'
    assert task.priority == 'H'
    assert 'tag1' in task.tags
    assert 'tag2' in task.tags
    assert task.due == '20230101T000000Z'


def test_modifytask(mock_config, mock_taskwarrior_cmd):
    """Test modifytask function."""
    # Set return value for modify command
    mock_taskwarrior_cmd.set_return_value('task 1 modify', 0, 'Modified 1 task.', '')

    # Set return value for export command (to get the task)
    mock_taskwarrior_cmd.set_return_value('task export 1', 0, json.dumps([
        {
            'id': 1,
            'description': 'Updated task',
            'status': 'pending',
            'priority': 'M',
            'project': 'test',
            'tags': ['tag1', 'tag2']
        }
    ]), '')

    # Modify task
    task = modifytask(
        1,
        description='Updated task',
        priority='M',
        project='test',
        tagsadd=['tag1', 'tag2']
    )

    # Check task
    assert task is not None
    assert task.id == 1
    assert task.description == 'Updated task'
    assert task.priority == 'M'
    assert task.project == 'test'
    assert 'tag1' in task.tags
    assert 'tag2' in task.tags

    # Test removing tags
    mock_taskwarrior_cmd.set_return_value('task 1 modify', 0, 'Modified 1 task.', '')

    # Set return value for export command
    mock_taskwarrior_cmd.set_return_value('task export 1', 0, json.dumps([
        {
            'id': 1,
            'description': 'Updated task',
            'status': 'pending',
            'priority': 'M',
            'project': 'test',
            'tags': ['tag1']
        }
    ]), '')

    # Modify task to remove tag
    task = modifytask(
        1,
        tagsremove=['tag2']
    )

    # Check task
    assert task is not None
    assert 'tag1' in task.tags
    assert 'tag2' not in task.tags


def test_completetask(mock_config, mock_taskwarrior_cmd):
    """Test completetask function."""
    # Set return value for done command
    mock_taskwarrior_cmd.set_return_value('task 1 done', 0, 'Completed 1 task.', '')

    # Complete task
    success = completetask(1)

    # Check result
    assert success is True

    # Test failure
    mock_taskwarrior_cmd.set_return_value('task 999 done', 1, '', 'No task with ID 999 found.')

    # Complete non-existent task
    success = completetask(999)

    # Check result
    assert success is False


def test_deletetask(mock_config, mock_taskwarrior_cmd):
    """Test deletetask function."""
    # Set return value for delete command
    mock_taskwarrior_cmd.set_return_value('task 1 delete', 0, 'Deleted 1 task.', '')

    # Delete task
    success = deletetask(1)

    # Check result
    assert success is True

    # Check input was provided (to confirm deletion)
    cmd, kwargs = mock_taskwarrior_cmd.commands[0]
    assert 'input' in kwargs
    assert 'yes' in kwargs['input']

    # Test failure
    mock_taskwarrior_cmd.set_return_value('task 999 delete', 1, '', 'No task with ID 999 found.')

    # Delete non-existent task
    success = deletetask(999)

    # Check result
    assert success is False
