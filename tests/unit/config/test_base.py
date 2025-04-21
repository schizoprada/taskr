# ~/taskr/tests/unit/config/test_base.py
"""Tests for the config base module."""
import os
import pytest
import yaml
import uuid
from pathlib import Path

from taskr.config.base import Config, DEFAULT


# Use a completely isolated config for each test
@pytest.fixture
def isolated_config_path(temp_dir):
    """Create a unique config path for completely isolated tests."""
    unique_id = uuid.uuid4().hex
    config_path = os.path.join(temp_dir, f'test_config_{unique_id}.yaml')
    if os.path.exists(config_path):
        os.remove(config_path)
    return config_path

def test_config_init(isolated_config_path):
    """Test Config initialization."""
    # Delete any existing file to ensure we start fresh
    if os.path.exists(isolated_config_path):
        os.remove(isolated_config_path)

    # Initialize config with isolated path
    config = Config(isolated_config_path)

    # Check that the config file was created
    assert os.path.exists(isolated_config_path)

    # Read the file directly to verify contents
    with open(isolated_config_path, 'r') as f:
        config_data = yaml.safe_load(f)

    # Check that default values were written correctly
    assert config_data['taskwarrior']['command'] == 'task'

    # Now check the loaded config
    assert config.config['taskwarrior']['command'] == 'task'

def test_config_init_existing(isolated_config_path):
    """Test Config initialization with existing file."""
    # Create a config file
    test_config = {
        'taskwarrior': {
            'command': 'custom_task',
            'data': {
                'location': '/custom/path'
            }
        }
    }

    with open(isolated_config_path, 'w') as f:
        yaml.dump(test_config, f)

    # Initialize config
    config = Config(isolated_config_path)

    # Check that values were loaded
    assert config.config['taskwarrior']['command'] == 'custom_task'
    assert config.config['taskwarrior']['data']['location'] == '/custom/path'

    # Check that default values were merged for missing sections
    assert 'display' in config.config
    assert 'shortcuts' in config.config

def test_config_get(isolated_config_path):
    """Test getting config values."""
    # Delete any existing file to ensure we start fresh
    if os.path.exists(isolated_config_path):
        os.remove(isolated_config_path)

    # Create a fresh default config file
    default_config = DEFAULT.CONFIG.VALUES.copy()
    os.makedirs(os.path.dirname(isolated_config_path), exist_ok=True)
    with open(isolated_config_path, 'w') as f:
        yaml.dump(default_config, f)

    # Initialize a fresh config with isolated path
    config = Config(isolated_config_path)

    # Test getting sections
    taskwarrior_section = config.get('taskwarrior')
    assert isinstance(taskwarrior_section, dict)
    assert taskwarrior_section['command'] == 'task'

    # Test getting specific values
    assert config.get('taskwarrior', 'command') == 'task'

    # Test getting non-existent values
    assert config.get('nonexistent') == {}
    assert config.get('taskwarrior', 'nonexistent') is None


def test_config_set(isolated_config_path):
    """Test setting config values."""
    # Initialize config with isolated path
    config = Config(isolated_config_path)

    # Set a value
    config.set('taskwarrior', 'command', 'custom_task')
    assert config.get('taskwarrior', 'command') == 'custom_task'

    # Set a value in a new section
    config.set('new_section', 'key', 'value')
    assert config.get('new_section', 'key') == 'value'


def test_config_save(isolated_config_path):
    """Test saving config."""
    # Initialize config with isolated path
    config = Config(isolated_config_path)

    # Modify config
    config.set('taskwarrior', 'command', 'custom_task')
    config.set('new_section', 'key', 'value')

    # Save config
    config.save()

    # Read config file directly
    with open(isolated_config_path, 'r') as f:
        loaded_config = yaml.safe_load(f)

    # Check values
    assert loaded_config['taskwarrior']['command'] == 'custom_task'
    assert loaded_config['new_section']['key'] == 'value'


def test_config_merge_defaults(isolated_config_path):
    """Test merging default config values."""
    # Create a config file with partial data
    test_config = {
        'taskwarrior': {
            'command': 'custom_task'
        },
        'display': {
            'theme': 'light'
        }
    }

    with open(isolated_config_path, 'w') as f:
        yaml.dump(test_config, f)

    # Initialize config
    config = Config(isolated_config_path)

    # Check custom values
    assert config.get('taskwarrior', 'command') == 'custom_task'
    assert config.get('display', 'theme') == 'light'

    # Check default values were merged
    assert 'data' in config.get('taskwarrior')
    assert 'date' in config.get('display')
    assert 'time' in config.get('display')

    # Check other default sections were added
    assert 'shortcuts' in config.config
