from task import TaskCheck
from base_executor import exec_check_common
from exec_lua.lua_utils import lua_utils
from utils import TaskResult


def exec_check(task: TaskCheck, model: str, run: int) -> TaskResult:
    """
    Execute a TaskCheck for Lua code.
    Returns a TaskResult containing success/failure status and any errors.
    """
    return exec_check_common(task, model, run, lua_utils)