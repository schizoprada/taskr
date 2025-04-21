# ~/taskr/src/taskr/config/manager.py
import os, yaml, typing as t
from pathlib import Path

from taskr.logs import log
from taskr.config.base import DEFAULT
from taskr.config.schema import TaskrConfig, validateconfig

class ConfigManager:
    """Enhanced configuration manager with validation."""

    def __init__(self, configpath: t.Optional[str] = None):
        """
        Initialize the configuration manager.

        Args:
            configpath: Path to the configuration file.
                      If None, the default path will be used.
        """
        self.configdir = DEFAULT.CONFIG.DIR
        self.configpath = configpath or os.path.join(self.configdir, DEFAULT.CONFIG.FILE)
        self._config = None
        self._load()

    def _load(self) -> None:
        """Load configuration from file and validate it."""
        # Create default config directory if it doesn't exist
        os.makedirs(self.configdir, exist_ok=True)

        # If config file doesn't exist, create it with default values
        if not os.path.exists(self.configpath):
            self._createdefault()

        # Load and parse config file
        try:
            with open(self.configpath, 'r') as f:
                configdict = yaml.safe_load(f) or {}

            # Validate configuration
            self._config = validateconfig(configdict)
        except Exception as e:
            log.error(f"exception loading configuration: {str(e)}")
            # Create a default config if there's an error
            self._config = TaskrConfig()

    def _createdefault(self) -> None:
        """Create a default configuration file."""
        try:
            defaultconfig = TaskrConfig().dict()
            with open(self.configpath, 'w') as f:
                yaml.dump(defaultconfig, f, default_flow_style=False)
            log.info(f"created default configuration at {self.configpath}")
        except Exception as e:
            log.error(f"exception creating default configuration: {str(e)}")

    def save(self) -> None:
        """Save the current configuration to file."""
        try:
            configdict = self._config.dict()
            with open(self.configpath, 'w') as f:
                yaml.dump(configdict, f, default_flow_style=False)
        except Exception as e:
            log.error(f"exception saving configuration: {str(e)}")

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
        if not hasattr(self._config, section):
            # Handle custom section
            if section == "custom":
                if key:
                    return self._config.custom.get(key)
                return self._config.custom
            return None

        sectiondata = getattr(self._config, section)

        if key is None:
            return sectiondata

        # Handle nested attributes
        parts = key.split('.')
        value = sectiondata

        for part in parts:
            if hasattr(value, part):
                value = getattr(value, part)
            elif hasattr(value, "__getitem__") and part in value:
                value = value[part]
            else:
                return None

        return value

    def set(self, section: str, key: str, value: t.Any) -> None:
        """
        Set a configuration value.

        Args:
            section: Configuration section.
            key: Configuration key within the section.
            value: Value to set.
        """
        if hasattr(self._config, section):
            # Handle nested attributes
            parts = key.split('.')
            sectiondata = getattr(self._config, section)

            if len(parts) == 1:
                # Direct attribute
                if hasattr(sectiondata, key):
                    setattr(sectiondata, key, value)
                    return
            else:
                # Nested attribute
                target = sectiondata
                for i, part in enumerate(parts[:-1]):
                    if hasattr(target, part):
                        target = getattr(target, part)
                    else:
                        break
                else:
                    # All parts exist, set the final value
                    lastpart = parts[-1]
                    if hasattr(target, lastpart):
                        setattr(target, lastpart, value)
                        return

        # Handle custom section for unknown paths
        if section == "custom":
            self._config.custom[key] = value
        else:
            # Create nested dict in custom if needed
            if section not in self._config.custom:
                self._config.custom[section] = {}

            self._config.custom[section][key] = value

    def getall(self) -> t.Dict[str, t.Any]:
        """
        Get the entire configuration.

        Returns:
            Dict containing the configuration.
        """
        return self._config.dict()

    def reset(self) -> None:
        """Reset configuration to defaults."""
        self._config = TaskrConfig()
        self.save()


# Singleton config manager instance
configmanager = ConfigManager()
