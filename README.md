# Taskr

An enhanced CLI wrapper for [TaskWarrior](https://taskwarrior.org/) featuring interactive prompts and rich terminal output.

![Version](https://img.shields.io/badge/version-0.2.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## Overview

Taskr enhances the TaskWarrior experience by providing:

- **Interactive prompts** for adding, modifying, and managing tasks
- **Rich terminal output** with tables, colors, and formatting
- **Simplified command structure** with intuitive shortcuts
- **Interactive filtering** to quickly find tasks
- **Backup and restore capabilities** to protect your data

## Installation

### Prerequisites

- Python 3.8+
- [TaskWarrior](https://taskwarrior.org/)

### Install from PyPI
```bash
pip install taskr
```

### Install from source

```bash
git clone https://github.com/schizoprada/taskr.git
cd taskr
pip install -e .
```

## Configuration

Taskr uses a YAML-based configuration system. The default configuration is created at `~/.taskr/config.yaml` on first run.

### Configuration Options

- **TaskWarrior settings**: Command path, data location
- **Display settings**: Theme, date formats, colors
- **Shortcuts**: Customize command shortcuts
- **Filters**: Save commonly used task filters

### Edit configuration

```bash
taskr config edit
```

Or use the interactive configuration editor:

```bash
taskr config interactive
```

## Usage

Taskr commands are designed to be intuitive and interactive by default. Most commands will launch an interactive prompt if no arguments are provided.

### Adding Tasks

```bash
taskr add                  # Interactive prompt (default)
taskr add "Task description" --project work --priority H
taskr add --no-interactive "Task description" --due tomorrow
```

### Listing Tasks

```bash
taskr list                 # Interactive filter selection (default)
taskr list today           # Show tasks due today
taskr list week            # Show tasks due this week
taskr list overdue         # Show overdue tasks
taskr list --project work  # List tasks in work project
```

### Completing Tasks

```bash
taskr done                 # Interactive task selection (default)
taskr done 5               # Complete task #5
```

### Task Info

```bash
taskr info                 # Interactive task selection (default)
taskr info 5               # Show details for task #5
```

### Modifying Tasks

```bash
taskr modify               # Interactive task selection and modification (default)
taskr modify 5 --project home --priority M
taskr modify 5 --add-tag important --remove-tag waiting
```

### Deleting Tasks

```bash
taskr delete               # Interactive task selection (default)
taskr delete 5 --force     # Delete task #5 without confirmation
```

### Backup and Restore

```bash
taskr backup               # Create a backup
taskr backup export tasks.json  # Export tasks to JSON
taskr backup all           # Backup both data and export tasks
```

## Shortcuts

Taskr provides convenient shortcuts for common commands:

```
a  → add
l  → list
d  → done
m  → modify
del → delete
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
