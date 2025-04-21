# ~/taskr/src/taskr/config/schema.py
import os, typing as t
from pydantic import BaseModel, Field, validator

class TaskwarriorData(BaseModel):
    """TaskWarrior data configuration."""

    location: str = Field(
        default="~/.task",
        description="Location of TaskWarrior data directory"
    )

    @validator("location")
    def expandpath(cls, v):
        """Expand user path in location."""
        if v:
            return os.path.expanduser(v)
        return v


class TaskwarriorConfig(BaseModel):
    """TaskWarrior configuration settings."""

    command: str = Field(
        default="task",
        description="The TaskWarrior command to use"
    )

    data: TaskwarriorData = Field(
        default_factory=TaskwarriorData,
        description="TaskWarrior data settings"
    )

    udas: t.Optional[t.Dict[str, t.Any]] = Field(
        default=None,
        description="User-defined attributes configuration"
    )


class DisplayTimeConfig(BaseModel):
    """Time display configuration."""

    format: str = Field(
        default="HH:mm",
        description="Format for displaying times"
    )


class DisplayDateConfig(BaseModel):
    """Date display configuration."""

    format: str = Field(
        default="YYYY-MM-DD",
        description="Format for displaying dates"
    )


class DisplayConfig(BaseModel):
    """Display and UI configuration settings."""

    theme: str = Field(
        default="dark",
        description="The UI theme to use"
    )

    date: DisplayDateConfig = Field(
        default_factory=DisplayDateConfig,
        description="Date formatting settings"
    )

    time: DisplayTimeConfig = Field(
        default_factory=DisplayTimeConfig,
        description="Time formatting settings"
    )

    prioritycolors: t.Dict[str, str] = Field(
        default={
            "H": "red",
            "M": "yellow",
            "L": "blue",
            "": "white"
        },
        description="Colors for different priority levels"
    )

    showtags: bool = Field(
        default=True,
        description="Whether to show tags in task listings"
    )


class ShortcutsConfig(BaseModel):
    """Command shortcuts configuration."""

    add: str = Field(
        default="a",
        description="Shortcut for adding a task"
    )

    list: str = Field(
        default="l",
        description="Shortcut for listing tasks"
    )

    done: str = Field(
        default="d",
        description="Shortcut for completing a task"
    )

    delete: str = Field(
        default="del",
        description="Shortcut for deleting a task"
    )

    modify: str = Field(
        default="m",
        description="Shortcut for modifying a task"
    )


class FilterConfig(BaseModel):
    """Task filtering configuration."""

    defaultfilters: t.List[str] = Field(
        default=["status:pending"],
        description="Default filters to apply when listing tasks"
    )

    savedfilters: t.Dict[str, t.List[str]] = Field(
        default={
            "today": ["+SCHEDULED", "+TODAY", "or", "+DUE", "+TODAY"]
        },
        description="Saved filters that can be used by name"
    )


class TaskrConfig(BaseModel):
    """Main Taskr configuration schema."""

    taskwarrior: TaskwarriorConfig = Field(
        default_factory=TaskwarriorConfig,
        description="TaskWarrior configuration settings"
    )

    display: DisplayConfig = Field(
        default_factory=DisplayConfig,
        description="Display and UI configuration settings"
    )

    shortcuts: ShortcutsConfig = Field(
        default_factory=ShortcutsConfig,
        description="Command shortcuts configuration"
    )

    filters: FilterConfig = Field(
        default_factory=FilterConfig,
        description="Task filtering configuration"
    )

    custom: t.Dict[str, t.Any] = Field(
        default_factory=dict,
        description="Custom user-defined configuration values"
    )


def validateconfig(configdict: t.Dict[str, t.Any]) -> TaskrConfig:
    """
    Validate configuration against the schema.

    Args:
        configdict: Configuration dictionary to validate.

    Returns:
        Validated configuration object.
    """
    return TaskrConfig(**configdict)
