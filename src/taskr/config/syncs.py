# ~/taskr/src/taskr/config/syncs.py
import os, typing as t, dataclasses as dc
from pydantic import BaseModel, Field

from taskr.logs import log
from taskr.config import getconfig, setconfig


class SyncTargetConfig(BaseModel):

    exportsenabled: bool = Field(
        default=True,
        description="Whether exporting to this target is enabled"
    )

    exportsauto: bool = Field(
        default=False,
        description="Whether to automatically export after changes"
    )

    importsenabled: bool = Field(
        default=True,
        description="Whether importing from this target is enabled"
    )

    importsauto: bool = Field(
        default=False,
        description="Whether to automatically import on startup"
    )

    options: t.Dict[str, t.Any] = Field(
        default_factory=dict,
        description="Target-specific options"
    )


class SyncConfig(BaseModel):

    taskd: SyncTargetConfig = Field(
        default_factory=lambda: SyncTargetConfig(exportsenabled=True, exportsauto=False, importsenabled=False, importsauto=False),
        description="Taskd Sync Configuration"
    )

    reminders: SyncTargetConfig = Field(
        default_factory=lambda: SyncTargetConfig(exportsenabled=True, exportsauto=False, importsenabled=True, importsauto=False),
        description="Apple Reminders Sync Configuration"
    )


def getsyncsconfig() -> SyncConfig:
    configdata = getconfig("syncs")
    if not configdata:
        configdata = SyncConfig().dict()
        setconfig("syncs", None, configdata)
    return SyncConfig(**configdata)

def gettargetconfig(target: str) -> t.Optional[SyncTargetConfig]:
    toplevel = getsyncsconfig()
    if hasattr(toplevel, target):
        return getattr(toplevel, target)
    return None

def updatetargetconfig(target: str, **kwargs) -> bool:
    toplevel = getsyncsconfig()
    if not hasattr(toplevel, target):
        return False

    targetconfig = getattr(toplevel, target)
    for k, v in kwargs.items():
        if hasattr(targetconfig, k):
            setattr(targetconfig, k, v)

    configdict = toplevel.dict()
    setconfig("syncs", None, configdict)
    return True



"""yaml

targets:
    taskd:
        exports:
            enabled: true
            auto: true # auto sync after any changes made

    reminders:
        exports:
            enabled: true
            auto: true
        imports:
            enabled: true
            auto: false

"""

@dc.dataclass
class SyncsConfig:
    pass
