from typing import Union
from task import TaskCall, TaskContains, TaskRun, TaskCheck, Language
from utils import TaskResult
from exec_rust import exec_call as rust_exec_call, exec_contains as rust_exec_contains, exec_run as rust_exec_run, exec_check as rust_exec_check
from exec_swift import exec_call as swift_exec_call, exec_contains as swift_exec_contains, exec_run as swift_exec_run, exec_check as swift_exec_check
from exec_typescript import exec_call as ts_exec_call, exec_contains as ts_exec_contains, exec_run as ts_exec_run, exec_check as ts_exec_check
from exec_python import exec_call as py_exec_call, exec_contains as py_exec_contains, exec_run as py_exec_run, exec_check as py_exec_check
from exec_php import exec_call as php_exec_call, exec_contains as php_exec_contains, exec_run as php_exec_run, exec_check as php_exec_check
from exec_lua import exec_call as lua_exec_call, exec_contains as lua_exec_contains, exec_run as lua_exec_run, exec_check as lua_exec_check
from exec_go import exec_call as go_exec_call, exec_contains as go_exec_contains, exec_run as go_exec_run, exec_check as go_exec_check
from exec_kotlin import exec_call as kotlin_exec_call, exec_contains as kotlin_exec_contains, exec_run as kotlin_exec_run, exec_check as kotlin_exec_check
from exec_csharp import exec_call as csharp_exec_call, exec_contains as csharp_exec_contains, exec_run as csharp_exec_run, exec_check as csharp_exec_check


class Executor:
    def __init__(self, language: Language):
        self.language = language

    def call(
        self,
        task: Union[TaskCall, TaskContains, TaskRun, TaskCheck],
        model: str,
        run: int,
    ) -> TaskResult:
        if isinstance(task, TaskCall):
            return self._exec_call(task, model, run)
        elif isinstance(task, TaskContains):
            return self._exec_contains(task, model, run)
        elif isinstance(task, TaskRun):
            return self._exec_run(task, model, run)
        elif isinstance(task, TaskCheck):
            return self._exec_check(task, model, run)
        else:
            raise ValueError(f"Unsupported task type: {task.__class__.__name__}")

    def _exec_call(self, task: TaskCall, model: str, run: int) -> TaskResult:
        if self.language == Language.RUST:
            return rust_exec_call(task, model, run)
        elif self.language == Language.SWIFT:
            return swift_exec_call(task, model, run)
        elif self.language == Language.TYPESCRIPT:
            return ts_exec_call(task, model, run)
        elif self.language == Language.PYTHON:
            return py_exec_call(task, model, run)
        elif self.language == Language.PHP:
            return php_exec_call(task, model, run)
        elif self.language == Language.LUA:
            return lua_exec_call(task, model, run)
        elif self.language == Language.GO:
            return go_exec_call(task, model, run)
        elif self.language == Language.KOTLIN:
            return kotlin_exec_call(task, model, run)
        elif self.language == Language.CSHARP:
            return csharp_exec_call(task, model, run)
        else:
            raise ValueError(f"Unsupported language: {self.language}")

    def _exec_contains(self, task: TaskContains, model: str, run: int) -> TaskResult:
        if self.language == Language.RUST:
            return rust_exec_contains(task, model, run)
        elif self.language == Language.SWIFT:
            return swift_exec_contains(task, model, run)
        elif self.language == Language.TYPESCRIPT:
            return ts_exec_contains(task, model, run)
        elif self.language == Language.PYTHON:
            return py_exec_contains(task, model, run)
        elif self.language == Language.PHP:
            return php_exec_contains(task, model, run)
        elif self.language == Language.LUA:
            return lua_exec_contains(task, model, run)
        elif self.language == Language.GO:
            return go_exec_contains(task, model, run)
        elif self.language == Language.KOTLIN:
            return kotlin_exec_contains(task, model, run)
        elif self.language == Language.CSHARP:
            return csharp_exec_contains(task, model, run)
        else:
            raise ValueError(f"Unsupported language: {self.language}")

    def _exec_run(self, task: TaskRun, model: str, run: int) -> TaskResult:
        if self.language == Language.RUST:
            return rust_exec_run(task, model, run)
        elif self.language == Language.SWIFT:
            return swift_exec_run(task, model, run)
        elif self.language == Language.TYPESCRIPT:
            return ts_exec_run(task, model, run)
        elif self.language == Language.PYTHON:
            return py_exec_run(task, model, run)
        elif self.language == Language.PHP:
            return php_exec_run(task, model, run)
        elif self.language == Language.LUA:
            return lua_exec_run(task, model, run)
        elif self.language == Language.GO:
            return go_exec_run(task, model, run)
        elif self.language == Language.KOTLIN:
            return kotlin_exec_run(task, model, run)
        elif self.language == Language.CSHARP:
            return csharp_exec_run(task, model, run)
        else:
            raise ValueError(f"Unsupported language: {self.language}")

    def _exec_check(self, task: TaskCheck, model: str, run: int) -> TaskResult:
        if self.language == Language.RUST:
            return rust_exec_check(task, model, run)
        elif self.language == Language.SWIFT:
            return swift_exec_check(task, model, run)
        elif self.language == Language.TYPESCRIPT:
            return ts_exec_check(task, model, run)
        elif self.language == Language.PYTHON:
            return py_exec_check(task, model, run)
        elif self.language == Language.PHP:
            return php_exec_check(task, model, run)
        elif self.language == Language.LUA:
            return lua_exec_check(task, model, run)
        elif self.language == Language.GO:
            return go_exec_check(task, model, run)
        elif self.language == Language.KOTLIN:
            return kotlin_exec_check(task, model, run)
        elif self.language == Language.CSHARP:
            return csharp_exec_check(task, model, run)
        else:
            raise ValueError(f"Unsupported language: {self.language}")
