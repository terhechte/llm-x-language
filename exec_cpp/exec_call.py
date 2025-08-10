from task import TaskCall
from base_executor import exec_call_common
from exec_cpp.cpp_utils import cpp_utils
from utils import TaskResult

def exec_call(task: TaskCall, model: str, run: int) -> TaskResult:
    return exec_call_common(task, model, run, cpp_utils)