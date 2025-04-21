# ~/taskr/src/taskr/config/utils.py
import os, yaml, typing as t
from pathlib import Path

from taskr.logs import log
from taskr.config.manager import configmanager

def getconfigpath() -> str:
    """
    Get the path to the configuration file.

    Returns:
        Path to the configuration file.
    """
    return configmanager.configpath


def ensureconfigdir() -> str:
    """
    Ensure that the configuration directory exists.

    Returns:
        Path to the configuration directory.
    """
    configdir = os.path.dirname(configmanager.configpath)
    os.makedirs(configdir, exist_ok=True)
    return configdir


def backupconfig() -> t.Optional[str]:
    """
    Create a backup of the current configuration file.

    Returns:
        Path to the backup file, or None if backup failed.
    """
    configpath = configmanager.configpath
    if not os.path.exists(configpath):
        return None

    backuppath = f"{configpath}.bak"
    try:
        with open(configpath, 'r') as src:
            with open(backuppath, 'w') as dst:
                dst.write(src.read())
        return backuppath
    except Exception as e:
        log.error(f"exception creating backup: {str(e)}")
        return None


def restorebackup() -> bool:
    """
    Restore configuration from backup.

    Returns:
        True if backup was successfully restored, False otherwise.
    """
    configpath = configmanager.configpath
    backuppath = f"{configpath}.bak"

    if not os.path.exists(backuppath):
        return False

    try:
        with open(backuppath, 'r') as src:
            with open(configpath, 'w') as dst:
                dst.write(src.read())

        # Reload configuration
        configmanager._load()
        return True
    except Exception as e:
        log.error(f"exception restoring backup: {str(e)}")
        return False


def exportconfig(exportpath: str) -> bool:
    """
    Export configuration to a file.

    Args:
        exportpath: Path to export the configuration to.

    Returns:
        True if export was successful, False otherwise.
    """
    try:
        configdict = configmanager.getall()
        with open(exportpath, 'w') as f:
            yaml.dump(configdict, f, default_flow_style=False)
        return True
    except Exception as e:
        log.error(f"exception exporting configuration: {str(e)}")
        return False


def importconfig(importpath: str) -> bool:
    """
    Import configuration from a file.

    Args:
        importpath: Path to import the configuration from.

    Returns:
        True if import was successful, False otherwise.
    """
    if not os.path.exists(importpath):
        return False

    try:
        # Create backup before import
        backupconfig()

        # Import configuration
        with open(importpath, 'r') as f:
            configdict = yaml.safe_load(f) or {}

        # Write to config file
        with open(configmanager.configpath, 'w') as f:
            yaml.dump(configdict, f, default_flow_style=False)

        # Reload configuration
        configmanager._load()
        return True
    except Exception as e:
        log.error(f"exception importing configuration: {str(e)}")
        # Try to restore backup
        restorebackup()
        return False


def getsectionkeys(section: str) -> t.List[str]:
    """
    Get all keys in a configuration section.

    Args:
        section: Configuration section.

    Returns:
        List of keys in the section.
    """
    sectiondata = configmanager.get(section)
    if sectiondata is None:
        return []

    if hasattr(sectiondata, "__dict__"):
        # Handle Pydantic model
        return list(sectiondata.__dict__.keys())
    elif isinstance(sectiondata, dict):
        # Handle dictionary
        return list(sectiondata.keys())
    else:
        return []


def findconfigvalue(keyquery: str) -> t.List[t.Tuple[str, str, t.Any]]:
    """
    Find configuration values matching a key query.

    Args:
        keyquery: Key query to search for.

    Returns:
        List of tuples (section, key, value) matching the query.
    """
    results = []
    configdict = configmanager.getall()

    # Flatten the config dict
    flattened = _flattendict(configdict)

    # Search for matches
    for key, value in flattened.items():
        if keyquery.lower() in key.lower():
            # Split the key into section and remainder
            parts = key.split('.', 1)
            if len(parts) == 2:
                section, keypart = parts
                results.append((section, keypart, value))

    return results


def _flattendict(d: dict, prefix: str = '') -> dict:
    """
    Flatten a nested dictionary with dot notation.

    Args:
        d: Dictionary to flatten.
        prefix: Current key prefix.

    Returns:
        Flattened dictionary.
    """
    if not isinstance(d, dict):
        return {}

    result = {}
    for k, v in d.items():
        key = f"{prefix}.{k}" if prefix else k

        if isinstance(v, dict):
            # Recursively flatten nested dicts
            nested = _flattendict(v, key)
            result.update(nested)
        else:
            # Add leaf values
            result[key] = v

    return result


def mergeconfigs(baseconfig: dict, overlayconfig: dict) -> dict:
    """
    Merge two configuration dictionaries, with overlay taking precedence.

    Args:
        baseconfig: Base configuration.
        overlayconfig: Overlay configuration.

    Returns:
        Merged configuration.
    """
    result = baseconfig.copy()

    for k, v in overlayconfig.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = mergeconfigs(result[k], v)
        else:
            result[k] = v

    return result
