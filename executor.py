from typing import Union
from task import TaskCall, TaskContains, TaskRun, TaskCheck, Language
from utils import TaskResult
import exec_rust
import exec_swift
import exec_typescript
import exec_python


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
            return exec_rust.exec_call(task, model, run)
        elif self.language == Language.SWIFT:
            return exec_swift.exec_call(task, model, run)
        elif self.language == Language.TYPESCRIPT:
            return exec_typescript.exec_call(task, model, run)
        elif self.language == Language.PYTHON:
            return exec_python.exec_call(task, model, run)
        else:
            raise ValueError(f"Unsupported language: {self.language}")

    def _exec_contains(self, task: TaskContains, model: str, run: int) -> TaskResult:
        if self.language == Language.RUST:
            return exec_rust.exec_contains(task, model, run)
        elif self.language == Language.SWIFT:
            return exec_swift.exec_contains(task, model, run)
        elif self.language == Language.TYPESCRIPT:
            return exec_typescript.exec_contains(task, model, run)
        elif self.language == Language.PYTHON:
            return exec_python.exec_contains(task, model, run)
        else:
            raise ValueError(f"Unsupported language: {self.language}")

    def _exec_run(self, task: TaskRun, model: str, run: int) -> TaskResult:
        if self.language == Language.RUST:
            return exec_rust.exec_run(task, model, run)
        elif self.language == Language.SWIFT:
            return exec_swift.exec_run(task, model, run)
        elif self.language == Language.TYPESCRIPT:
            return exec_typescript.exec_run(task, model, run)
        elif self.language == Language.PYTHON:
            return exec_python.exec_run(task, model, run)
        else:
            raise ValueError(f"Unsupported language: {self.language}")

    def _exec_check(self, task: TaskCheck, model: str, run: int) -> TaskResult:
        if self.language == Language.RUST:
            return exec_rust.exec_check(task, model, run)
        elif self.language == Language.SWIFT:
            return exec_swift.exec_check(task, model, run)
        elif self.language == Language.TYPESCRIPT:
            return exec_typescript.exec_check(task, model, run)
        elif self.language == Language.PYTHON:
            return exec_python.exec_check(task, model, run)
        else:
            raise ValueError(f"Unsupported language: {self.language}")
