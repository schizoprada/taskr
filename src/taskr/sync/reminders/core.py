# ~/taskr/src/taskr/sync/reminders/core.py
import re, enum, typing as t, dataclasses as dc
from datetime import datetime, timedelta

from taskr.logs import log
from taskr.interface.task import Task

class OsaDate(str):
    _pattern = re.compile(
        r"""^
        (?:(?P<weekday>[A-Za-z]+),\s*)?
        (?P<month>[A-Za-z]+)\s+(?P<day>\d{1,2}),\s+(?P<year>\d{4})
        (?:\s+at\s+(?P<hour>\d{1,2}):(?P<minute>\d{2})(?::(?P<second>\d{2}))?\s*(?P<ampm>[APap][Mm])?)?
        $
        """,
        re.VERBOSE
    )

    def __new__(cls, value: str) -> 'OsaDate':
        if not cls._pattern.fullmatch(value):
            raise ValueError(f"Invalid OsaDate: {value}")
        return str.__new__(cls, value)

    def todatetime(self) -> datetime:
        raise NotImplementedError


    @classmethod
    def isosadate(cls, value: str) -> bool:
        return bool(cls._pattern.fullmatch(value))

    @classmethod
    def FromDatetime(cls, dt: datetime) -> 'OsaDate':
        """
        Apple Dates Format:
            [Day of Week], [Month] [Day], [Year] at [HH:MM:SS] [AM/PM]

        [HH:MM:SS] [AM/PM] -> defaults to 12:00:00 AM if None
        """
        weekday, month, meridian = (dt.strftime(fmt) for fmt in ("%A", "%B", "%p"))
        timestamp = dt.time().replace(microsecond=0)
        return cls(f"{weekday}, {month} {dt.day}, {dt.year} at {timestamp} {meridian}")


def isosadate(value: t.Any) -> bool:
    if value is None:
        return False
    if isinstance(value, OsaDate):
        return True
    if isinstance(value, str):
        return OsaDate.isosadate(value)
    return False

class OsaIndices(str, enum.Enum):
    FIRST = "first"
    LAST = "last"
    SOME = "some"
    EVERY = "every"


@dc.dataclass
class Reminder:
    """Dataclass representation of AppleScript Reminder Object"""
    name: str
    body: t.Optional[str] = None
    listname: t.Optional[str] = None
    duedate: t.Optional[datetime] = None
    priority: int = 0
    completed: bool = False
    completiondate: t.Optional[datetime] = None
    creationdate: t.Optional[datetime] = None
    modificationdate: t.Optional[datetime] = None
    id: t.Optional[str] = None # UUID
    remindmedate: t.Optional[datetime] = None
    flagged: bool = False



    @property
    def osaduedate(self) -> t.Optional[OsaDate]:
        if self.duedate:
            return OsaDate.FromDatetime(self.duedate)
        return None

    @property
    def osacompletiondate(self) -> t.Optional[OsaDate]:
        if self.completiondate:
            return OsaDate.FromDatetime(self.completiondate)
        return None

    @property
    def osacreationdate(self) -> t.Optional[OsaDate]:
        if self.creationdate:
            return OsaDate.FromDatetime(self.creationdate)
        return None

    @property
    def osamodificationdate(self) -> t.Optional[OsaDate]:
        if self.modificationdate:
            return OsaDate.FromDatetime(self.modificationdate)
        return None

    @property
    def osaremindmedate(self) -> t.Optional[OsaDate]:
        if self.remindmedate:
            return OsaDate.FromDatetime(self.remindmedate)
        return None


    def totask(self, **kwargs) -> Task:
        taskdata = {
            "description": self.name,
            "status": "completed" if self.completed else "pending"
        }
        annotations = []
        if self.body:
            annotations.append({"description": self.body})

        if self.priority:
            if self.priority >= 7:
                taskdata['priority'] = "H"
            elif self.priority >= 4:
                taskdata['priority'] = "M"
            elif self.priority > 0:
                taskdata["priority"] = "L"

        if self.duedate:
            taskdata["due"] = self.duedate.strftime("%Y-%m-%d")

        tags = []

        if self.listname and self.listname != 'Reminders':
            taskdata["project"] = self.listname
            tags.append(self.listname)

        if self.flagged:
            tags.append("critical")

        if tags:
            taskdata["tags"] = tags

        udas = {"reminder_id": self.id} if self.id else {}

        task = Task(
            **taskdata,
            annotations=annotations,
            udas=udas
        )
        return task

    def osaproperties(self) -> dict:
        properties = {"name": self.name}
        if self.body:
            properties["body"] = self.body
        if self.duedate:
            properties["due date"] = self.duedate
        if self.priority:
            properties["priority"] = self.priority
        if self.flagged:
            properties["flagged"] = self.flagged
        return properties


    @classmethod
    def FromTask(cls, task: Task) -> 'Reminder':
        reminderid = task.udas.get("reminder_id") if hasattr(task, "udas") else None

        priority = 0
        if task.priority:
            priority = {"H": 9, "M": 5, "L": 1}.get(task.priority, 0)

        duedate = None
        if task.due:
            if isinstance(task.due, str):
                try:
                    # Handle different TaskWarrior date formats
                    if len(task.due) == 8 and task.due.isdigit():
                        # Format: YYYYMMDD
                        duedate = datetime.strptime(task.due, "%Y%m%d")
                    elif len(task.due) >= 10 and 'T' in task.due:
                        # Format: YYYYMMDDTHHMMSSZ
                        # Extract just the date part before the T
                        datepart = task.due.split('T')[0]
                        if len(datepart) == 8:
                            duedate = datetime.strptime(datepart, "%Y%m%d")
                        else:
                            log.error(f"Unrecognized date format: {task.due}")
                    elif len(task.due) >= 10:
                        # Format: YYYY-MM-DD
                        duedate = datetime.strptime(task.due[:10], "%Y-%m-%d")
                    else:
                        log.error(f"Unrecognized date format: {task.due}")
                except Exception as e:
                    log.error(f"error parsing task due date ({task.due}): {str(e)}")
            else:
                duedate = task.due

        body = None
        if task.annotations and len(task.annotations) > 0:
            body = task.annotations[0].get("description", "")

        listname = None
        if task.project:
            listname = task.project

        reminder = cls(
            name=task.description,
            body=body,
            listname=listname,
            duedate=duedate,
            priority=priority,
            completed=(task.status == 'completed'),
            id=reminderid,
            flagged=("critical" in (task.tags or []))
        )

        return reminder

    @classmethod
    def FromPropertiesDict(cls, properties: dict) -> 'Reminder':
        data = {}
        clsfields = dc.fields(cls)
        for key, value in properties.items():
            if key in [field.name for field in clsfields]:
                if value is not None:
                    if isosadate(value):
                        data[key] = OsaDate(value).todatetime()
                    else:
                        data[key] = value
            else:
                catkey = "".join(key.split())
                if catkey in [field.name for field in clsfields]:
                    if value is not None:
                        if isosadate(value):
                            data[catkey] = OsaDate(value).todatetime()
                        else:
                            data[catkey] = value
        return cls(**data)
