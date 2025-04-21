# ~/taskr/tests/unit/config/test_utils.py
"""Tests for the config utility functions."""
import os
import pytest
import yaml
import shutil
from pathlib import Path

from taskr.config.utils import (
    getconfigpath,
    ensureconfigdir,
    backupconfig,
    restorebackup,
    exportconfig,
    importconfig,
    getsectionkeys,
    findconfigvalue,
    mergeconfigs
)


def test_get_config_path(mock_config):
    """Test getconfigpath function."""
    # Get config path
    path = getconfigpath()

    # Check path
    assert isinstance(path, str)
    assert path.endswith('config.yaml')


def test_ensure_config_dir(mock_config, temp_dir, monkeypatch):
    """Test ensureconfigdir function."""
    # Create a test directory path that doesn't exist yet
    test_config_dir = os.path.join(temp_dir, f'test_config_dir_{os.getpid()}')

    # Patch the config manager's config path to use our test directory
    from taskr.config.manager import configmanager
    original_path = configmanager.configpath
    configmanager.configpath = os.path.join(test_config_dir, 'config.yaml')

    try:
        # Ensure config dir
        created_dir = ensureconfigdir()

        # Check directory was created
        assert os.path.exists(created_dir)
        assert os.path.isdir(created_dir)
    finally:
        # Restore original path
        configmanager.configpath = original_path
        # Clean up
        if os.path.exists(test_config_dir):
            shutil.rmtree(test_config_dir)


def test_backup_config(mock_config):
    """Test backupconfig function."""
    # Backup config
    backup_path = backupconfig()

    # Check backup was created
    assert backup_path is not None
    assert os.path.exists(backup_path)

    # Check backup content
    with open(backup_path, 'r') as f:
        backup_content = f.read()

    with open(getconfigpath(), 'r') as f:
        original_content = f.read()

    assert backup_content == original_content


def test_restore_backup(mock_config):
    """Test restorebackup function."""
    # Create a backup
    backup_path = backupconfig()
    assert backup_path is not None

    # Modify the original config
    config_path = getconfigpath()
    with open(config_path, 'r') as f:
        config_data = yaml.safe_load(f)

    config_data['taskwarrior']['command'] = 'modified_command'

    with open(config_path, 'w') as f:
        yaml.dump(config_data, f)

    # Restore backup
    success = restorebackup()

    # Check restore was successful
    assert success is True

    # Check config was restored
    with open(config_path, 'r') as f:
        restored_config = yaml.safe_load(f)

    assert restored_config['taskwarrior']['command'] != 'modified_command'


def test_export_config(mock_config, temp_dir):
    """Test exportconfig function."""
    # Set a unique value to identify the export
    from taskr.config import setconfig
    setconfig('custom', 'export_test', 'test_value')

    # Export config
    export_path = os.path.join(temp_dir, 'exported_config.yaml')
    success = exportconfig(export_path)

    # Check export was successful
    assert success is True
    assert os.path.exists(export_path)

    # Check export content
    with open(export_path, 'r') as f:
        exported_config = yaml.safe_load(f)

    assert exported_config['custom']['export_test'] == 'test_value'


def test_import_config(mock_config, temp_dir):
    """Test importconfig function."""
    # Create a config file to import
    import_config = {
        'taskwarrior': {
            'command': 'imported_command',
            'data': {
                'location': '/imported/path'
            }
        },
        'custom': {
            'import_test': 'test_value'
        }
    }

    import_path = os.path.join(temp_dir, 'import_config.yaml')
    with open(import_path, 'w') as f:
        yaml.dump(import_config, f)

    # Import config
    success = importconfig(import_path)

    # Check import was successful
    assert success is True

    # Check config was imported
    from taskr.config import getconfig
    assert getconfig('taskwarrior', 'command') == 'imported_command'
    assert getconfig('custom', 'import_test') == 'test_value'


def test_get_section_keys(mock_config):
    """Test getsectionkeys function."""
    # Get keys for taskwarrior section
    keys = getsectionkeys('taskwarrior')

    # Check keys
    assert isinstance(keys, list)
    assert 'command' in keys
    assert 'data' in keys

    # Get keys for non-existent section
    empty_keys = getsectionkeys('nonexistent')
    assert empty_keys == []


def test_find_config_value(mock_config, monkeypatch):
    """Test findconfigvalue function."""
    from taskr.config.utils import findconfigvalue, _flattendict

    # Create direct test data
    test_data = {
        'taskwarrior': {
            'command': 'test_command'
        },
        'display': {
            'theme': 'test_theme'
        },
        'shortcuts': {
            'add': 'test_add'
        }
    }

    # Directly test the flattening function
    flattened = _flattendict(test_data)
    assert 'taskwarrior.command' in flattened
    assert flattened['taskwarrior.command'] == 'test_command'

    # Mock the getall method of configmanager
    from taskr.config.manager import configmanager

    def mock_getall():
        return test_data

    monkeypatch.setattr(configmanager, 'getall', mock_getall)

    # Now test findconfigvalue directly
    results = findconfigvalue('test')

    # Check that we found results
    assert isinstance(results, list)
    assert len(results) >= 3

    # Verify specific expected results
    result_values = [(s, k, v) for s, k, v in results]
    assert ('taskwarrior', 'command', 'test_command') in result_values
    assert ('display', 'theme', 'test_theme') in result_values
    assert ('shortcuts', 'add', 'test_add') in result_values


def test_merge_configs():
    """Test mergeconfigs function."""
    # Create base config
    base_config = {
        'section1': {
            'key1': 'value1',
            'key2': 'value2'
        },
        'section2': {
            'key1': 'value1'
        }
    }

    # Create overlay config
    overlay_config = {
        'section1': {
            'key2': 'new_value',
            'key3': 'value3'
        },
        'section3': {
            'key1': 'value1'
        }
    }

    # Merge configs
    merged_config = mergeconfigs(base_config, overlay_config)

    # Check merged config
    assert merged_config['section1']['key1'] == 'value1'  # Kept from base
    assert merged_config['section1']['key2'] == 'new_value'  # Updated from overlay
    assert merged_config['section1']['key3'] == 'value3'  # Added from overlay
    assert merged_config['section2']['key1'] == 'value1'  # Kept from base
    assert merged_config['section3']['key1'] == 'value1'  # Added from overlay
