# ~/taskr/src/taskr/sync/base.py
import abc, typing as t

from taskr.logs import log
from taskr.config.syncs import gettargetconfig


class SyncManager(abc.ABC):
    def __init__(self, name: str, canimport: bool = False, canexport: bool = False) -> None:
        self.name = name
        self._canimport = canimport
        self._canexport = canexport
        self.exportsenabled = False
        self.exportsauto = False
        self.importsenabled = False
        self.importsauto = False
        self.options = {}
        self._loadconfig()

    def _loadconfig(self) -> None:
        config = gettargetconfig(self.name.lower())
        if config:
            self.exportsenabled = config.exportsenabled if self._canexport else False
            self.exportsauto = config.exportsauto if self._canexport else False
            self.importsenabled = config.importsenabled if self._canimport else False
            self.importsauto = config.importsauto if self._canimport else False
            self.options = config.options
        else:
            self.exportsenabled = self._canexport
            self.exportsauto = False
            self.importsenabled = self._canimport
            self.importsauto = False
            self.options = {}

    def canimport(self) -> bool:
        return (self._canimport and self.importsenabled)

    def canexport(self) -> bool:
        return (self._canexport and self.exportsenabled)

    def shouldautoimport(self) -> bool:
        return (self.canimport() and self.importsauto)

    def shouldautoexport(self) -> bool:
        return (self.canexport() and self.exportsauto)

    def getoption(self, key: str, default: t.Any = None) -> t.Any:
        return self.options.get(key, default)

    def _imports(self, *args, **kwargs) -> int:
        """Override with subclasses"""
        return 0

    def _exports(self, *args, **kwargs) -> int:
        """Override with subclasses"""
        return 0

    def imports(self, *args, **kwargs) -> int:
        if not self.canimport():
            log.warning(f"({self.name}) sync target does not support importing")
            return 0
        return self._imports(*args, **kwargs)

    def exports(self, *args, **kwargs) -> int:
        if not self.canexport():
            log.warning(f"({self.name}) sync target does not support exporting")
            return 0
        return self._exports(*args, **kwargs)
