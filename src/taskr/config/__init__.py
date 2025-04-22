# ~/taskr/src/taskr/config/__init__.py 
"""
Taskr configuration package.

This package provides configuration management for Taskr,
including loading, validation, and access to configuration values.
"""

from .base import Config, config, DEFAULT
from .schema import (
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
from .manager import ConfigManager, configmanager
from .utils import (
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

__all__ = [
    # Base configuration
    'Config',
    'config',
    'DEFAULT',

    # Schema classes
    'TaskrConfig',
    'TaskwarriorConfig',
    'TaskwarriorData',
    'DisplayConfig',
    'DisplayDateConfig',
    'DisplayTimeConfig',
    'ShortcutsConfig',
    'FilterConfig',
    'validateconfig',

    # Enhanced configuration management
    'ConfigManager',
    'configmanager',

    # Utility functions
    'getconfigpath',
    'ensureconfigdir',
    'backupconfig',
    'restorebackup',
    'exportconfig',
    'importconfig',
    'getsectionkeys',
    'findconfigvalue',
    'mergeconfigs'
]

import typing as t
def getconfig(section: t.Optional[str] = None, key: t.Optional[str] = None, usemanager: bool = True):
    """
    Get a configuration value.

    This function provides a unified interface to access configuration values
    from either the basic config or the enhanced config manager.

    Args:
        section: Configuration section.
        key: Configuration key within the section.
             If None, the entire section will be returned.
        usemanager: Whether to use the config manager (True) or basic config (False).

    Returns:
        Configuration value, section, or the entire configuration if both
        section and key are None.
    """
    if usemanager:
        source = configmanager
    else:
        source = config

    if section is None:
        # Return the entire configuration
        return source.getall() if hasattr(source, 'getall') else source.config

    return source.get(section, key)


def setconfig(section: str, key: str, value, usemanager: bool = True) -> None:
    """
    Set a configuration value.

    This function provides a unified interface to set configuration values
    using either the basic config or the enhanced config manager.

    Args:
        section: Configuration section.
        key: Configuration key within the section.
        value: Value to set.
        usemanager: Whether to use the config manager (True) or basic config (False).
    """
    if usemanager:
        configmanager.set(section, key, value)
        configmanager.save()
    else:
        config.set(section, key, value)
        config.save()


def saveconfig(usemanager: bool = True) -> None:
    """
    Save configuration.

    This function provides a unified interface to save the configuration
    using either the basic config or the enhanced config manager.

    Args:
        usemanager: Whether to use the config manager (True) or basic config (False).
    """
    if usemanager:
        configmanager.save()
    else:
        config.save()
