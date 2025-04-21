# ~/taskr/src/taskr/logs.py
from __future__ import annotations
import sys, inspect, logging, typing as t
from logging import StreamHandler, FileHandler, Formatter
from dataclasses import dataclass, field, asdict
from colorama import Fore, Style, init

init(autoreset=True) # initialize colorama, auto-reset colors after each print

class FMT(Formatter):
    COLORS = {
        "DEBUG": Fore.CYAN,
        "INFO": Fore.GREEN,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "CRITICAL": Fore.MAGENTA

    }

    def _resolveclassname(self, outer, funcname: str) -> str:
        classname = ""
        if ("self" in outer.frame.f_locals):
            return f"{outer.frame.f_locals['self'].__class__.__name__}."
        elif ("cls" in outer.frame.f_locals):
            return f"{outer.frame.f_locals['cls'].__class__.__name__}."
        else:
            try:
                qualname = outer.frame.f_globals[funcname].__qualname__
                if ('.' in qualname):
                    return f"{qualname.split('.')[-2]}."
            except Exception as e:
                pass
        return classname

    def format(self, record) -> str:

        # retrieve caller details
        frame = inspect.currentframe()
        outerframes = inspect.getouterframes(frame)

        # frame index to capture original caller
        frameidx = min(8, (len(outerframes) - 1))
        outer = outerframes[frameidx]
        funcname = outer.function

        classname = self._resolveclassname(outer, funcname)

        color = self.COLORS.get(record.levelname, Fore.WHITE)

        caller = f"{classname}{funcname}".ljust(21)
        level = record.levelname.ljust(min(8, len(record.levelname)))
        coloredlevel = f"{color}{level}{Style.RESET_ALL}"

        msg = f"{caller} | {coloredlevel} | {record.getMessage()}"

        return msg


def logger(name: str, level: int = logging.DEBUG, console: bool = True, path: t.Optional[str] = None, propagate: bool = False) -> logging.Logger:
    """
    Configures and returns a logger with the specified name.
    This logger can output to console and/or a file with colored formatting.

    Parameters:
      - name (str): Logger name.
      - level (int): Logging level (e.g., logging.DEBUG, logging.INFO).
      - console (bool): Whether to output logs to the console (stdout).
      - path (str): Path to a log file. If None, no file handler is added.
      - propagate (bool): Whether to propagate logs to ancestor loggers.

    Returns:
      - logging.Logger: Configured logger instance.
    """

    log = logging.getLogger(name)
    log.setLevel(level)
    log.propagate = propagate

    log.handlers = [] # clear handlers

    if console:
        consolehandler = StreamHandler(sys.stdout)
        consolehandler.setLevel(level)
        consolehandler.setFormatter(FMT())
        log.addHandler(consolehandler)

    if path:
        filehandler = FileHandler(path)
        filehandler.setLevel(level)
        filehandler.setFormatter(FMT())
        log.addHandler(filehandler)

    return log

log = logger('taskr', level=logging.INFO)

__all__ = ['log']
