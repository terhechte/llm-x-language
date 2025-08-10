from task import TaskCall
from base_executor import exec_call_common
from exec_zig.zig_utils import zig_utils
from utils import TaskResult

def exec_call(task: TaskCall, model: str, run: int) -> TaskResult:
    return exec_call_common(task, model, run, zig_utils)