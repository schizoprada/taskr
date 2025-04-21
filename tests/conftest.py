# ~/taskr/tests/conftest.py
import os
import pytest
import tempfile
import shutil
import yaml
from pathlib import Path

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def temp_config_dir(temp_dir):
    """Create a temporary config directory with default config."""
    config_dir = os.path.join(temp_dir, '.taskr')
    os.makedirs(config_dir, exist_ok=True)

    # Create default config file
    config_file = os.path.join(config_dir, 'config.yaml')
    default_config = {
        "taskwarrior": {
            "command": "task",
            "data": {
                "location": os.path.join(temp_dir, '.task')
            },
        },
        "display": {
            "theme": "dark",
            "date": {
                "format": "YYYY-MM-DD"
            },
            "time": {
                "format": "HH:mm"
            },
            "prioritycolors": {
                "H": "red",
                "M": "yellow",
                "L": "blue",
                "": "white"
            },
            "showtags": True
        },
        "shortcuts": {
            "add": "a",
            "list": "l",
            "done": "d",
            "delete": "del",
            "modify": "m",
        },
        "filters": {
            "defaultfilters": ["status:pending"],
            "savedfilters": {
                "today": ["+SCHEDULED", "+TODAY", "or", "+DUE", "+TODAY"]
            }
        },
        "custom": {}
    }

    with open(config_file, 'w') as f:
        yaml.dump(default_config, f, default_flow_style=False)

    # Create TaskWarrior data dir
    task_dir = os.path.join(temp_dir, '.task')
    os.makedirs(task_dir, exist_ok=True)

    return config_dir

@pytest.fixture
def mock_taskwarrior_cmd(monkeypatch):
    """Mock the TaskWarrior command execution."""

    class MockSubprocess:
        def __init__(self):
            self.commands = []
            self.return_values = {}

        def set_return_value(self, cmd_pattern, return_code, stdout, stderr):
            """Set return value for a command pattern."""
            self.return_values[cmd_pattern] = (return_code, stdout, stderr)

        def run(self, cmd, **kwargs):
            """Mock subprocess.run."""
            self.commands.append((cmd, kwargs))

            # Find matching command pattern
            matching_pattern = None
            for pattern in self.return_values:
                if pattern in ' '.join(cmd):
                    matching_pattern = pattern
                    break

            # Create mock result
            class MockResult:
                pass

            result = MockResult()

            if matching_pattern:
                return_code, stdout, stderr = self.return_values[matching_pattern]
            else:
                # Default to success
                return_code, stdout, stderr = 0, "", ""

            result.returncode = return_code
            result.stdout = stdout
            result.stderr = stderr

            if return_code != 0 and kwargs.get('check', False):
                class MockCalledProcessError(Exception):
                    def __init__(self, returncode, cmd, output=None, stderr=None):
                        self.returncode = returncode
                        self.cmd = cmd
                        self.output = output
                        self.stdout = output
                        self.stderr = stderr

                raise MockCalledProcessError(return_code, cmd, stdout, stderr)

            return result

    mock_subp = MockSubprocess()
    monkeypatch.setattr("subprocess.run", mock_subp.run)

    return mock_subp

@pytest.fixture(scope="function")
def mock_config(monkeypatch, temp_config_dir):
    """Mock the config module to use temporary config."""

    # First we'll need to import before patching
    import taskr.config.base

    # Store original values
    original_dir = taskr.config.base.DEFAULT.CONFIG.DIR
    original_config = taskr.config.base.config

    # Patch DEFAULT.CONFIG.DIR
    monkeypatch.setattr(taskr.config.base.DEFAULT.CONFIG, "DIR", temp_config_dir)

    # Create new Config instance with temp path
    config_file = os.path.join(temp_config_dir, 'config.yaml')
    test_config = taskr.config.base.Config(config_file)

    # Patch the singleton
    monkeypatch.setattr("taskr.config.base.config", test_config)

    # Reimport to get patched config
    import importlib
    importlib.reload(taskr.config)

    yield test_config

    # Restore original values after test
    monkeypatch.setattr(taskr.config.base.DEFAULT.CONFIG, "DIR", original_dir)
    monkeypatch.setattr("taskr.config.base.config", original_config)
    importlib.reload(taskr.config)


@pytest.fixture(autouse=True)
def reset_singleton_config():
    """Reset all singleton config instances before each test to ensure isolation."""
    import importlib
    import sys

    # Get all config modules that might have singletons
    config_modules = [mod for name, mod in sys.modules.items()
                     if name.startswith('taskr.config')]

    # Save the originals
    originals = {}
    for mod in config_modules:
        for name, obj in vars(mod).items():
            if name in ['config', 'configmanager']:
                originals[(mod.__name__, name)] = obj

    yield

    # Restore originals after test
    for (mod_name, name), obj in originals.items():
        mod = sys.modules.get(mod_name)
        if mod:
            setattr(mod, name, obj)

    # Reload the config modules
    for mod in config_modules:
        importlib.reload(mod)
