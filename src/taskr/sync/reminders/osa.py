# ~/taskr/src/taskr/sync/reminders/osa.py
"""
Osascript interface
"""
import os, json, enum, typing as t, dataclasses as dc, subprocess as sub, traceback as tb
from datetime import datetime
from taskr.logs import log
from taskr.sync.reminders.core import Reminder, OsaDate, isosadate, OsaIndices

class CMD:
    class OPS:
        CREATE: str = "make new reminder"
        READ: str = "get"
        UPDATE: str = "set"
        DELETE: str = "delete"

    class TARGET:
        BYNAME: str = 'reminder whose name is "{name}"'
        BYINDEX: str = '{index} reminder' # verbal index e.g. 'first'

        INLIST: str = 'in list "{name}"'
        ATLIST: str = 'at list "{name}"'

    class PROPERTY:
        GET: str = ""


class DEFAULT:
    PROPERTIES: list = ["name", "body", "due date", "priority", "completed", "id", "flagged"]



class osascript:
    class COMMANDS:
        GETLIST: str  = 'tell application "Reminders" to get name of lists'
        CREATELIST: str  = 'tell application "Reminders" to make new list with properties {{name:"{name}"}}'

    @staticmethod
    def execute(command: str) -> t.Any:
        try:

            result = sub.run(
                ["osascript", "-e", command],
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode != 0:
                log.error(f"AppleScript execution failed: {result.stderr}")
                return None

            output = result.stdout.strip()
            if output:
                try:
                    if output.startswith('{') or output.startswith('['):
                       return json.loads(output)
                    return output
                except json.JSONDecodeError:
                    return output
            return True
        except Exception as e:
            log.error(f"exception executing AppleScript: {str(e)}")
            return None

    @classmethod
    def getlists(cls) -> t.List[str]:
        result = []
        output = cls.execute(cls.COMMANDS.GETLIST)
        if not output:
            return result

        if isinstance(output, str):
            return [name.strip() for name in output.split(",")]
        return result

    @classmethod
    def createlist(cls, name: str) -> bool:
        cmd = cls.COMMANDS.CREATELIST.format(name=name)
        return bool(cls.execute(cmd))

    @classmethod
    def getreminders(cls, listname: t.Optional[str] = None, properties: t.Optional[list] = None) -> t.List[Reminder]:
        properties = (properties or DEFAULT.PROPERTIES)
        builder = cls.builder().read(properties).byindex(OsaIndices.EVERY)
        if listname:
            builder.bylist(listname)
        cmd = builder.build()
        result = cmd.execute()
        if not result:
            return []
        parsed = cls.parse.reminderproperties(result, properties)
        reminders = [Reminder.FromPropertiesDict(data) for data in parsed]
        return reminders




    class parse:
        @staticmethod
        def reminderid(output: str) -> t.Optional[str]:
            if output and isinstance(output, str) and "reminder id" in output:
                return output.split("reminder id ")[1].strip()
            return None

        @staticmethod
        def reminderproperties(output: str, properties: list) -> t.List[t.Dict[str, t.Any]]:
            if (not output) or (output == "True"):
                return []
            values = []
            currentvalue = ""
            indate = False

            for char in output:
                if (char == ',') and (not indate):
                    values.append(currentvalue.strip())
                    currentvalue = ""
                else:
                    if (char == 'd') and (currentvalue.strip() == "date"):
                        indate = True
                    elif indate and (char == 'M'):
                        currentvalue += char
                        values.append(currentvalue.strip())
                        currentvalue = ""
                        indate = False
                    else:
                        currentvalue += char

            if currentvalue.strip():
                values.append(currentvalue.strip())

            if len(values) == len(properties):
                reminder = {}
                for i, prop in enumerate(properties):
                    reminder[prop] = values[i]
                return [reminder]

            result = []
            chunks = [values[i:i+len(properties)] for i in range(0, len(values), len(properties))]

            for chunk in chunks:
                if len(chunk) == len(properties):
                    reminder = {}
                    for i, prop in enumerate(properties):
                        reminder[prop] = chunk[i]
                    result.append(reminder)

            return result

    class builder:
        def __init__(self) -> None:
            self.listclause = None
            self.targetclause = None
            self.propertyname = None
            self.propertyvalue = None
            self.index = None
            self.properties: list = [] # properties to read
            self.propertyclauses: dict = {} # properties to write
            self.operation = None
            self.command = None

        def create(self) -> 'osascript.builder':
            self.operation = CMD.OPS.CREATE
            return self

        def read(self, properties=None) -> 'osascript.builder':
            self.operation = CMD.OPS.READ
            self.properties = (properties or DEFAULT.PROPERTIES)
            return self

        def update(self, name, value) -> 'osascript.builder':
            self.operation = CMD.OPS.UPDATE
            self.propertyname = name
            self.propertyvalue = value
            return self

        def delete(self) -> 'osascript.builder':
            self.operation = CMD.OPS.DELETE
            return self

        def bylist(self, name: str) -> 'osascript.builder':
            if name:
                if self.operation is not None:
                    if self.operation == CMD.OPS.CREATE:
                        self.listclause = f' at list "{name}"'
                    else:
                        self.listclause = f' of list "{name}"'
            return self


        def byname(self, name: str) -> 'osascript.builder':
            self.targetclause = f' whose name is "{name}"'
            return self

        def byindex(self, index: t.Union[str, OsaIndices] = OsaIndices.FIRST) -> 'osascript.builder':
            if not isinstance(index, OsaIndices):
                try:
                    index = OsaIndices[index]
                except Exception:
                    log.warning(f"invalid index ({index}), defaulting to {OsaIndices.FIRST}")
                    index = OsaIndices.FIRST
            self.index = index.value
            return self

        def withproperties(self, properties: t.Optional[dict] = None, **kwargs) -> 'osascript.builder':
            properties = (properties or {})
            properties.update(kwargs)
            self.propertyclauses = properties # could add some validation logic in the future
            return self

        def _formatproperties(self) -> str:
            props = []
            for k, v in self.propertyclauses.items():
                formatted = self._formatvalue(v)
                props.append(f"{k}:{formatted}")
            return ", ".join(props)

        def _formatvalue(self, value: t.Any) -> str:
            if value is None:
                return "missing value"
            elif isinstance(value, bool):
                return "true" if value else "false"
            elif isinstance(value, (int, float)):
                return str(value)
            elif isinstance(value, datetime):
                osadate = OsaDate.FromDatetime(value)
                return f'date "{osadate}"'
            elif isosadate(value):
                return f'date "{value}"'
            elif isinstance(value, str):
                return f'"{value.replace('"', '\\"')}"'
            else:
                return f'"{str(value)}"'

        def _buildtarget(self) -> str:
            parts = []
            if self.index is not None:
                parts.append(self.index)

            parts.append("reminder")

            if self.listclause is not None:
                parts.append(self.listclause)
            if self.targetclause is not None:
                parts.append(self.targetclause)

            return " ".join(parts)

        def build(self, application: str = "Reminders") -> 'osascript.builder':
            if self.operation is None:
                log.warning(f"operation not yet set, cannot build")
                return self

            result = None
            listclause = (self.listclause or '')

            if self.operation == CMD.OPS.CREATE:
                propstr = self._formatproperties()
                result = f"{CMD.OPS.CREATE}{listclause} with properties {{{propstr}}}"
            elif self.operation == CMD.OPS.READ:
                propstr = ", ".join(self.properties)
                target = self._buildtarget()
                result = f"{CMD.OPS.READ} {{{propstr}}} of {target}"
            elif self.operation == CMD.OPS.UPDATE:
                target = self._buildtarget()
                value = self._formatvalue(self.propertyvalue)
                result = f"{CMD.OPS.UPDATE} {self.propertyname} of {target} to {value}"
            elif self.operation == CMD.OPS.DELETE:
                target = self._buildtarget()
                result = f"{CMD.OPS.DELETE} ({target})"

            if result is not None:
                command = f'tell application "{application}" to {result}'
                self.command = command

            return self

        def execute(self) -> t.Any:
            if self.command is None:
                log.warning(f"command not yet built, cannot execute")
                return None
            return osascript.execute(self.command)



"""
AppleScript Syntax for Reminders (via `osascript`)
---------------------------------------------------

General Structure:
    osascript -e 'tell application "Reminders" to <command>'

Reminder Properties:
    - name: string
    - body: string (notes)
    - due date: date object (e.g. date "April 22, 2024 at 6:00:00 PM")
    - priority: integer (0 = none, 1 = low, 5 = medium, 9 = high)
    - completed: boolean
    - flagged: boolean
    - remind me date: date
    - creation date / modification date: date (read-only)

Reminder Lists:
    - Default list is typically "Reminders"
    - Can create or query other named lists

Date Format:
    - "April 22, 2024 at 6:00:00 PM" (12-hour with AM/PM)
    - "April 22, 2024" defaults to 12:00:00 AM

---------------------------------------------------
Verbal Indexing:
---------------------------------------------------
Used to specify *which* item you’re referring to in a list.

Valid values:
    - `first` — the first matching reminder
    - `last` — the last matching reminder
    - `some` — a random one
    - `every` — all matching items (returns a list)

Example:
    - `first reminder of list "Reminders"` — selects the first reminder
    - `every reminder whose completed is false` — selects all uncompleted reminders
    - `delete (last reminder of list "Tasks" whose name is "Test")`

Note: Most modifying operations (`set`, `delete`) work best with `first` to avoid ambiguity.

---------------------------------------------------
Filtering with `whose` Clauses:
---------------------------------------------------
Use `whose` to filter reminders by properties — similar to SQL `WHERE` clause.

Basic structure:
    <type> whose <property> <operator> <value>

Examples:
    - `reminders whose name is "Buy milk"`
    - `reminders whose completed is false`
    - `reminders whose priority is 9`
    - `reminders whose due date < date "April 22, 2024 at 6:00:00 PM"`

Chained filters:
    - `reminders whose completed is false and priority is 9`
    - `first reminder of list "Reminders" whose name is "Submit report" and completed is false`

Limitations:
    - No support for arbitrary complex expressions (e.g., no OR or nested conditions)
    - Comparisons on dates can be finicky — better to cast explicitly to `date`

---------------------------------------------------
Example OsaScript Commands:
---------------------------------------------------

CREATE:
    osascript -e 'tell application "Reminders" to make new reminder in list "Reminders" with properties {name:"Buy milk", body:"Get whole milk", due date:date "Monday, April 22, 2024 at 6:00:00 PM", priority:5}'

READ:
    osascript -e 'tell application "Reminders" to get name of reminders in list "Reminders"'
    osascript -e 'tell application "Reminders" to get {name, completed, due date, id} of reminders in list "Reminders"'

UPDATE:
    osascript -e 'tell application "Reminders" to set completed of first reminder of list "Reminders" whose name is "Buy milk" to true'
    osascript -e 'tell application "Reminders" to set due date of first reminder whose name is "Buy milk" to date "Tuesday, April 23, 2024 at 10:00:00 AM"'

DELETE:
    osascript -e 'tell application "Reminders" to delete (first reminder of list "Reminders" whose name is "Buy milk")'

ADVANCED:

    LOOP:
        tell application "Reminders"
            set rlist to reminders of list "Reminders"
            repeat with r in rlist
                set rname to name of r
                set rid to id of r
                -- do something...
            end repeat
        end tell

    FILTERING:
        osascript -e 'tell application "Reminders" to get name of reminders in list "Tasks" whose completed is false and priority is 9'

    EXTRA:
        osascript -e 'tell application "Reminders" to get name of lists'
        osascript -e 'tell application "Reminders" to make new list with properties {name:"TaskwarriorSync"}'
"""
