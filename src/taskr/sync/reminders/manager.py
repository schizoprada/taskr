# ~/taskr/src/taskr/sync/reminders/manager.py
"""
Reminders Sync Manager
"""

import typing as t
from datetime import datetime

from taskr.logs import log
from taskr.interface import Task, tasklist
from taskr.sync.base import SyncManager
from taskr.sync.reminders.core import Reminder
from taskr.sync.reminders.osa import osascript


class ReminderSync(SyncManager):
    def __init__(self, listname: t.Optional[str] = None) -> None:
        super().__init__(name="Reminders", canimport=True, canexport=True)
        self.listname = listname
        self._ensurelistexists()

    def _ensurelistexists(self) -> None:
        if self.listname is not None:
            extant = osascript.getlists()
            if self.listname not in extant:
                log.debug(f"creating reminders list: {self.listname}")
                osascript.createlist(self.listname)



    def _updatereminder(self, reminder: Reminder) -> bool:
        if not reminder.id:
            return False

        try:

            properties = reminder.osaproperties()
            success = True

            for prop, value in properties.items():
                if self.listname:
                    cmd = osascript.builder().update(prop, value).byindex("first").bylist(self.listname).build()
                else:
                    cmd = osascript.builder().update(prop, value).byindex("first").build()
                if reminder.id:
                    cmd.command = cmd.command.replace("first reminder", f"reminder id {reminder.id}")
                else:
                    cmd.byname(reminder.name)

                result = cmd.execute()
                if not result:
                    success = False

            return success
        except Exception as e:
            log.error(f"exception updating reminder: {str(e)}")
            return False

    def _createreminder(self, reminder: Reminder) -> t.Optional[str]:
        try:
            properties = reminder.osaproperties()
            if self.listname:
                cmd = osascript.builder().create().bylist(self.listname).withproperties(properties).build()
            else:
                cmd = osascript.builder().create().withproperties(properties).build()

            result = cmd.execute()

            reminderid = osascript.parse.reminderid(result)
            return reminderid
        except Exception as e:
            log.error(f"exception creating reminder: {str(e)}")
            return None

    def _updatetask(self, task: Task) -> bool:
        from taskr.interface import modifytask

        try:
            if not task.id:
                return False

            annotations = None
            if task.annotations:
                annotations = [a for a in [a.get("description") for a in task.annotations if "description" in a] if a is not None]

            updated = modifytask(
                task.id,
                description=task.description,
                project=task.project,
                priority=task.priority,
                tagsadd=task.tags,
                due=task.due,
                annotations=annotations,
                udas=task.udas
            )
            return bool(updated)
        except Exception as e:
            log.error(f"exception updating task: {str(e)}")
            return False

    def _createtask(self, task: Task) -> bool:
        from taskr.interface import addtask

        try:
            new = addtask(
                description=task.description,
                project=task.project,
                priority=task.priority,
                tags=task.tags,
                due=task.due,
                udas=task.udas
            )

            if new and task.annotations:
                from taskr.interface import modifytask
                annotations = [a for a in [a.get("description") for a in task.annotations if "description" in a] if a is not None]
                modifytask(new.id, annotations=annotations)

            return bool(new)
        except Exception as e:
            log.error(f"exception creating task: {str(e)}")
            return False


    def _exports(self, filterargs: t.Optional[t.List[str]] = None) -> int:
        tasks = tasklist(filterargs=filterargs)
        if not tasks:
            log.debug(f"no tasks found for export")
            return 0

        extantreminders = osascript.getreminders(self.listname)
        extantids = {r.id for r in extantreminders if r.id}

        created = 0
        updated = 0

        for task in tasks:
            if not task.description:
                continue
            reminderid = task.udas.get("reminder_id") if hasattr(task, "udas") else None
            exists = (reminderid in extantids) if reminderid else False
            reminder = Reminder.FromTask(task)

            if exists:
                self._updatereminder(reminder)
                updated += 1
            else:
                newid = self._createreminder(reminder)
                if newid:
                    task.udas["reminder_id"] = newid
                    created += 1

        log.info(f"exported tasks ({created} created)  ({updated} updated)")

        return created + updated

    def _imports(self, completed: bool = False) -> int:
        reminders = osascript.getreminders(self.listname)
        if not reminders:
            log.info(f"no reminders found in '{self.listname}'")
            return 0

        if not completed:
            reminders = [r for r in reminders if not r.completed]

        tasks = tasklist(includeall=True)
        extantids = {}

        for task in tasks:
            if hasattr(task, "udas") and task.udas.get("reminder_id"):
                extantids[task.udas["reminder_id"]] = task.id

        created = 0
        updated = 0

        for reminder in reminders:
            if not reminder.id:
                continue

            task = reminder.totask()
            if reminder.id in extantids:
                task.id = extantids[reminder.id]
                self._updatetask(task)
                updated += 1
            else:
                self._createtask(task)
                created += 1

        log.info(f"imported tasks ({created} created)  ({updated} updated)")
        return created + updated
