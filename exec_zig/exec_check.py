from task import TaskCheck
from base_executor import exec_check_common
from exec_zig.zig_utils import zig_utils
from utils import TaskResult

def exec_check(task: TaskCheck, model: str, run: int) -> TaskResult:
    return exec_check_common(task, model, run, zig_utils)