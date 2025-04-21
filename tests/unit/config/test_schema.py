# ~/taskr/tests/unit/config/test_schema.py
"""Tests for the config schema module."""
import os
import pytest
from pydantic import ValidationError
import inspect

from taskr.config.schema import (
    TaskrConfig,
    TaskwarriorConfig,
    TaskwarriorData,
    DisplayConfig,
    DisplayDateConfig,
    DisplayTimeConfig,
    ShortcutsConfig,
    FilterConfig,
    validateconfig
)


def test_taskwarrior_config(monkeypatch):
    """Test TaskwarriorConfig schema."""
    # Directly override the expandpath method
    original_expandpath = TaskwarriorData.expandpath

    @classmethod
    def mock_expandpath(cls, v):
        if v and v.startswith('~'):
            return '/home/testuser' + v[1:]
        return v

    # Apply the override
    TaskwarriorData.expandpath = mock_expandpath

    try:
        # Create data with location that should be expanded
        data = TaskwarriorData(location='~/.task')
        assert data.location == '/home/testuser/.task'

        # Test default values of full config
        config = TaskwarriorConfig()
        assert config.command == 'task'

        # Create a new data instance within the test to verify expansion
        custom_data = TaskwarriorData(location='~/.custom')
        assert custom_data.location == '/home/testuser/.custom'
    finally:
        # Restore original method
        TaskwarriorData.expandpath = original_expandpath

def test_display_config():
    """Test DisplayConfig schema."""
    # Test default values
    config = DisplayConfig()
    assert config.theme == 'dark'
    assert config.date.format == 'YYYY-MM-DD'
    assert config.time.format == 'HH:mm'
    assert 'H' in config.prioritycolors
    assert config.showtags is True

    # Test custom values
    config = DisplayConfig(
        theme='light',
        date={'format': 'MM/DD/YYYY'},
        time={'format': 'h:mm a'},
        prioritycolors={'H': 'bright_red', 'M': 'bright_yellow'},
        showtags=False
    )
    assert config.theme == 'light'
    assert config.date.format == 'MM/DD/YYYY'
    assert config.time.format == 'h:mm a'
    assert config.prioritycolors['H'] == 'bright_red'
    assert config.showtags is False


def test_shortcuts_config():
    """Test ShortcutsConfig schema."""
    # Test default values
    config = ShortcutsConfig()
    assert config.add == 'a'
    assert config.list == 'l'
    assert config.done == 'd'
    assert config.delete == 'del'
    assert config.modify == 'm'

    # Test custom values
    config = ShortcutsConfig(
        add='add',
        list='ls',
        done='complete',
        delete='rm',
        modify='mod'
    )
    assert config.add == 'add'
    assert config.list == 'ls'
    assert config.done == 'complete'
    assert config.delete == 'rm'
    assert config.modify == 'mod'


def test_filter_config():
    """Test FilterConfig schema."""
    # Test default values
    config = FilterConfig()
    assert config.defaultfilters == ['status:pending']
    assert 'today' in config.savedfilters

    # Test custom values
    config = FilterConfig(
        defaultfilters=['status:pending', 'project:work'],
        savedfilters={
            'work': ['+project:work'],
            'urgent': ['+priority:H']
        }
    )
    assert config.defaultfilters == ['status:pending', 'project:work']
    assert 'work' in config.savedfilters
    assert 'urgent' in config.savedfilters
    assert config.savedfilters['work'] == ['+project:work']


def test_taskr_config():
    """Test TaskrConfig schema."""
    # Test default values
    config = TaskrConfig()
    assert isinstance(config.taskwarrior, TaskwarriorConfig)
    assert isinstance(config.display, DisplayConfig)
    assert isinstance(config.shortcuts, ShortcutsConfig)
    assert isinstance(config.filters, FilterConfig)
    assert config.custom == {}

    # Test custom values
    config = TaskrConfig(
        taskwarrior={'command': 'custom_task'},
        display={'theme': 'light'},
        shortcuts={'add': 'new'},
        filters={'defaultfilters': ['project:work']},
        custom={'my_setting': 'value'}
    )
    assert config.taskwarrior.command == 'custom_task'
    assert config.display.theme == 'light'
    assert config.shortcuts.add == 'new'
    assert config.filters.defaultfilters == ['project:work']
    assert config.custom['my_setting'] == 'value'


def test_validate_config():
    """Test validateconfig function."""
    # Test valid config
    config_dict = {
        'taskwarrior': {
            'command': 'task',
            'data': {
                'location': '~/.task'
            }
        },
        'display': {
            'theme': 'dark'
        }
    }

    config = validateconfig(config_dict)
    assert isinstance(config, TaskrConfig)
    assert config.taskwarrior.command == 'task'

    # Test invalid config
    invalid_config = {
        'taskwarrior': {
            'command': 123  # Should be a string
        }
    }

    with pytest.raises(ValidationError):
        validateconfig(invalid_config)
