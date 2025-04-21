# ~/taskr/tests/unit/config/test_manager.py
"""Tests for the config manager module."""
import os
import pytest
import yaml
from pathlib import Path

from taskr.config.manager import ConfigManager


def test_config_manager_init(temp_config_dir):
    """Test ConfigManager initialization."""
    # Initialize config manager
    manager = ConfigManager(os.path.join(temp_config_dir, 'config.yaml'))

    # Check that config was loaded
    assert manager._config is not None
    assert hasattr(manager._config, 'taskwarrior')
    assert hasattr(manager._config, 'display')


def test_config_manager_get(temp_config_dir):
    """Test getting config values from the manager."""
    # Initialize config manager
    manager = ConfigManager(os.path.join(temp_config_dir, 'config.yaml'))

    # Test getting sections
    taskwarrior_section = manager.get('taskwarrior')
    assert taskwarrior_section is not None
    assert hasattr(taskwarrior_section, 'command')

    # Test getting specific values
    assert manager.get('taskwarrior', 'command') == 'task'

    # Test getting nested attributes
    assert manager.get('taskwarrior', 'data.location') == os.path.join(temp_config_dir.replace('.taskr', '.task'))

    # Test getting non-existent values
    assert manager.get('nonexistent') is None
    assert manager.get('taskwarrior', 'nonexistent') is None


def test_config_manager_get_custom(temp_config_dir):
    """Test getting custom config values."""
    # Initialize config manager
    manager = ConfigManager(os.path.join(temp_config_dir, 'config.yaml'))

    # Set a custom value
    manager._config.custom['test_key'] = 'test_value'

    # Test getting the custom value
    assert manager.get('custom', 'test_key') == 'test_value'


def test_config_manager_set(temp_config_dir):
    """Test setting config values."""
    # Initialize config manager
    manager = ConfigManager(os.path.join(temp_config_dir, 'config.yaml'))

    # Set a direct attribute
    manager.set('taskwarrior', 'command', 'custom_task')
    assert manager.get('taskwarrior', 'command') == 'custom_task'

    # Set a nested attribute
    manager.set('taskwarrior', 'data.location', '/custom/path')
    assert manager.get('taskwarrior', 'data.location') == '/custom/path'

    # Set a custom value
    manager.set('custom', 'test_key', 'test_value')
    assert manager.get('custom', 'test_key') == 'test_value'

    # Set a value in a non-existent section
    manager.set('new_section', 'key', 'value')
    assert manager.get('custom', 'new_section')['key'] == 'value'


def test_config_manager_save(temp_config_dir):
    """Test saving config."""
    config_path = os.path.join(temp_config_dir, 'config.yaml')

    # Initialize config manager
    manager = ConfigManager(config_path)

    # Modify config
    manager.set('taskwarrior', 'command', 'custom_task')
    manager.set('custom', 'test_key', 'test_value')

    # Save config
    manager.save()

    # Read config file directly
    with open(config_path, 'r') as f:
        loaded_config = yaml.safe_load(f)

    # Check values
    assert loaded_config['taskwarrior']['command'] == 'custom_task'
    assert loaded_config['custom']['test_key'] == 'test_value'


def test_config_manager_getall(temp_config_dir):
    """Test getting all config values."""
    # Initialize config manager
    manager = ConfigManager(os.path.join(temp_config_dir, 'config.yaml'))

    # Get all config
    all_config = manager.getall()

    # Check structure
    assert isinstance(all_config, dict)
    assert 'taskwarrior' in all_config
    assert 'display' in all_config
    assert 'shortcuts' in all_config
    assert 'filters' in all_config
    assert 'custom' in all_config


def test_config_manager_reset(temp_config_dir):
    """Test resetting config to defaults."""
    config_path = os.path.join(temp_config_dir, 'config.yaml')

    # Initialize config manager
    manager = ConfigManager(config_path)

    # Modify config
    manager.set('taskwarrior', 'command', 'custom_task')
    manager.set('display', 'theme', 'custom_theme')

    # Reset config
    manager.reset()

    # Check values are back to defaults
    assert manager.get('taskwarrior', 'command') == 'task'
    assert manager.get('display', 'theme') == 'dark'

    # Check file was updated
    with open(config_path, 'r') as f:
        loaded_config = yaml.safe_load(f)

    assert loaded_config['taskwarrior']['command'] == 'task'
    assert loaded_config['display']['theme'] == 'dark'
