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
from exec_cpp import exec_call as cpp_exec_call, exec_contains as cpp_exec_contains, exec_run as cpp_exec_run, exec_check as cpp_exec_check
from exec_java import exec_call as java_exec_call, exec_contains as java_exec_contains, exec_run as java_exec_run, exec_check as java_exec_check
from exec_zig import exec_call as zig_exec_call, exec_contains as zig_exec_contains, exec_run as zig_exec_run, exec_check as zig_exec_check
from exec_scala import exec_call as scala_exec_call, exec_contains as scala_exec_contains, exec_run as scala_exec_run, exec_check as scala_exec_check
from base_executor import exec_call_common, exec_run_common, exec_check_common, exec_contains_common


class Executor:
    def __init__(self, language: Language):
        self.language = language
    
    def _get_language_utils(self):
        """Get the appropriate language utils for retry execution."""
        if self.language == Language.PYTHON:
            from exec_python.python_utils import python_utils
            return python_utils
        elif self.language == Language.RUST:
            from exec_rust.rust_utils import rust_utils
            return rust_utils
        elif self.language == Language.TYPESCRIPT:
            from exec_typescript.typescript_utils import typescript_utils
            return typescript_utils
        elif self.language == Language.SWIFT:
            from exec_swift.swift_utils import swift_utils
            return swift_utils
        elif self.language == Language.PHP:
            from exec_php.php_utils import php_utils
            return php_utils
        elif self.language == Language.LUA:
            from exec_lua.lua_utils import lua_utils
            return lua_utils
        elif self.language == Language.GO:
            from exec_go.go_utils import go_utils
            return go_utils
        elif self.language == Language.KOTLIN:
            from exec_kotlin.kotlin_utils import kotlin_utils
            return kotlin_utils
        elif self.language == Language.CSHARP:
            from exec_csharp.csharp_utils import csharp_utils
            return csharp_utils
        elif self.language == Language.CPP:
            from exec_cpp.cpp_utils import cpp_utils
            return cpp_utils
        elif self.language == Language.JAVA:
            from exec_java.java_utils import java_utils
            return java_utils
        elif self.language == Language.ZIG:
            from exec_zig.zig_utils import zig_utils
            return zig_utils
        elif self.language == Language.SCALA:
            from exec_scala.scala_utils import scala_utils
            return scala_utils
        else:
            return None

    def call(
        self,
        task: Union[TaskCall, TaskContains, TaskRun, TaskCheck],
        model: str,
        run: int,
        existing_code: str = None,
        existing_response: str = None,
    ) -> TaskResult:
        if isinstance(task, TaskCall):
            return self._exec_call(task, model, run, existing_code, existing_response)
        elif isinstance(task, TaskContains):
            return self._exec_contains(task, model, run, existing_code, existing_response)
        elif isinstance(task, TaskRun):
            return self._exec_run(task, model, run, existing_code, existing_response)
        elif isinstance(task, TaskCheck):
            return self._exec_check(task, model, run, existing_code, existing_response)
        else:
            raise ValueError(f"Unsupported task type: {task.__class__.__name__}")

    def _exec_call(self, task: TaskCall, model: str, run: int, existing_code: str = None, existing_response: str = None) -> TaskResult:
        # If we have existing code (retry case), use the common function directly
        if existing_code is not None and existing_response is not None:
            # Get the appropriate language utils
            utils = self._get_language_utils()
            if utils:
                return exec_call_common(task, model, run, utils, existing_code, existing_response)
        
        # Normal execution path
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
        elif self.language == Language.CPP:
            return cpp_exec_call(task, model, run)
        elif self.language == Language.JAVA:
            return java_exec_call(task, model, run)
        elif self.language == Language.ZIG:
            return zig_exec_call(task, model, run)
        elif self.language == Language.SCALA:
            return scala_exec_call(task, model, run)
        else:
            raise ValueError(f"Unsupported language: {self.language}")

    def _exec_contains(self, task: TaskContains, model: str, run: int, existing_code: str = None, existing_response: str = None) -> TaskResult:
        # If we have existing response (retry case), use the common function directly
        if existing_response is not None:
            utils = self._get_language_utils()
            if utils:
                return exec_contains_common(task, model, run, utils, existing_code, existing_response)
        
        # Normal execution path
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
        elif self.language == Language.CPP:
            return cpp_exec_contains(task, model, run)
        elif self.language == Language.JAVA:
            return java_exec_contains(task, model, run)
        elif self.language == Language.ZIG:
            return zig_exec_contains(task, model, run)
        elif self.language == Language.SCALA:
            return scala_exec_contains(task, model, run)
        else:
            raise ValueError(f"Unsupported language: {self.language}")

    def _exec_run(self, task: TaskRun, model: str, run: int, existing_code: str = None, existing_response: str = None) -> TaskResult:
        # If we have existing code (retry case), use the common function directly
        if existing_code is not None and existing_response is not None:
            utils = self._get_language_utils()
            if utils:
                return exec_run_common(task, model, run, utils, existing_code, existing_response)
        
        # Normal execution path
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
        elif self.language == Language.CPP:
            return cpp_exec_run(task, model, run)
        elif self.language == Language.JAVA:
            return java_exec_run(task, model, run)
        elif self.language == Language.ZIG:
            return zig_exec_run(task, model, run)
        elif self.language == Language.SCALA:
            return scala_exec_run(task, model, run)
        else:
            raise ValueError(f"Unsupported language: {self.language}")

    def _exec_check(self, task: TaskCheck, model: str, run: int, existing_code: str = None, existing_response: str = None) -> TaskResult:
        # If we have existing code (retry case), use the common function directly
        if existing_code is not None and existing_response is not None:
            utils = self._get_language_utils()
            if utils:
                return exec_check_common(task, model, run, utils, existing_code, existing_response)
        
        # Normal execution path
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
        elif self.language == Language.CPP:
            return cpp_exec_check(task, model, run)
        elif self.language == Language.JAVA:
            return java_exec_check(task, model, run)
        elif self.language == Language.ZIG:
            return zig_exec_check(task, model, run)
        elif self.language == Language.SCALA:
            return scala_exec_check(task, model, run)
        else:
            raise ValueError(f"Unsupported language: {self.language}")
