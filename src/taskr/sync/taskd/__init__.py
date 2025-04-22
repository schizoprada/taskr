# ~/taskr/src/taskr/sync/taskd/__init__.py
import typing as t, subprocess as sub

from taskr.logs import log
from taskr.sync.base import SyncManager

class TaskdSync(SyncManager):
    def __init__(self) -> None:
        super().__init__(name="Taskd", canimport=False, canexport=True)

    def _parseoutput(self, output: t.Optional[str] = None) -> int:
        if output is None:
            return 0
        lines = output.splitlines()
        targetline = next((line for line in lines if all(keyword in line for keyword in ("Sync", "changes"))), None)
        if targetline is None:
            return 0
        changes = next((word for word in targetline.split() if word.strip().isdigit()), None)
        if changes is not None:
            return int(changes)
        return 0

    def _exports(self) -> int:
        try:
            output = sub.run(
                ["task", "sync"],
                capture_output=True,
                text=True,
                check=False
            )
            #print(f"DEBUG: {output}")
            if output:
                result = "\n".join([output.stdout, output.stderr])
                return self._parseoutput(result)
            return 0
        except Exception as e:
            log.error(f"exception syncing with taskd: {str(e)}")
            return 0


if __name__ == "__main__":
    taskd = TaskdSync()
    changes = taskd.exports()
    print(f"Changes: {changes}")
