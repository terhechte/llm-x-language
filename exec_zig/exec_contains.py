from task import TaskContains
from base_executor import exec_contains_common
from exec_zig.zig_utils import zig_utils
from utils import TaskResult

def exec_contains(task: TaskContains, model: str, run: int) -> TaskResult:
    return exec_contains_common(task, model, run, zig_utils)