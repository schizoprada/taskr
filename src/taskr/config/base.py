# ~/taskr/src/taskr/config/base.py
import os, yaml, typing as t
from pathlib import Path

from taskr.logs import log

class DEFAULT:
    """Default configuration constants."""

    class CONFIG:
        """Configuration constants."""

        # Default configuration directory
        DIR = os.path.expanduser("~/.taskr")

        # Default configuration filename
        FILE = "config.yaml"

        # Default configuration values
        VALUES = {
            "taskwarrior": {
                "command": "task",
                "data": {
                   "location": "~/.task"
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
            },
            "shortcuts": {
                "add": "a",
                "list": "l",
                "done": "d",
                "delete": "del",
                "modify": "m",
            }
        }


class Config:
    """
    Base configuration handler.

    Loads, modifies, and saves Taskr configuration.
    """

    def __init__(self, path: t.Optional[str] = None) -> None:
        """
        Initialize the configuration handler.

        Args:
            path: Path to the configuration file.
                  If None, the default path will be used.
        """
        self.path = (path or os.path.join(DEFAULT.CONFIG.DIR, DEFAULT.CONFIG.FILE))
        self.config = self._load()

    def _createdefault(self) -> None:
        """
        Create a default configuration file.

        Writes the default configuration to the configuration file.
        """
        try:
            with open(self.path, 'w') as f:
                yaml.dump(DEFAULT.CONFIG.VALUES, f, default_flow_style=False)
        except Exception as e:
            log.error(f"exception creating default config: {str(e)}")

    def _mergedefaults(self, configdata: t.Dict[str, t.Any]) -> t.Dict[str, t.Any]:
        """
        Merge user configuration with default values.

        Ensures all required configuration values exist.

        Args:
            configdata: User configuration data.

        Returns:
            Merged configuration data.
        """
        result = DEFAULT.CONFIG.VALUES.copy()

        if configdata:
            for section, values in configdata.items():
                if section in result:
                    if isinstance(values, dict) and isinstance(result[section], dict):
                        result[section].update(values)
                    else:
                        result[section] = values
                else:
                    result[section] = values

        return result

    def _load(self) -> t.Dict[str, t.Any]:
        """
        Load configuration from file.

        Creates default configuration if the file doesn't exist.

        Returns:
            Configuration data.
        """
        os.makedirs(os.path.dirname(self.path), exist_ok=True)

        if not os.path.exists(self.path):
            self._createdefault()

        try:
            with open(self.path, 'r') as f:
               config = yaml.safe_load(f)

            return self._mergedefaults(config)
        except Exception as e:
            log.error(f"exception loading config: {str(e)}")
            return DEFAULT.CONFIG.VALUES

    def get(self, section: str, key: t.Optional[str] = None) -> t.Any:
        """
        Get a configuration value.

        Args:
            section: Configuration section.
            key: Configuration key within the section.
                 If None, the entire section will be returned.

        Returns:
            Configuration value or section.
        """
        if key is None:
            return self.config.get(section, {})
        return self.config.get(section, {}).get(key)

    def set(self, section: str, key: str, value: t.Any) -> None:
        """
        Set a configuration value.

        Args:
            section: Configuration section.
            key: Configuration key within the section.
            value: Value to set.
        """
        if section not in self.config:
            self.config[section] = {}

        self.config[section][key] = value

    def save(self) -> None:
        """
        Save configuration to file.

        Writes the current configuration to the configuration file.
        """
        try:
            with open(self.path, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False)
        except Exception as e:
            log.error(f"exception saving config: {str(e)}")


# Singleton configuration instance
config = Config()
