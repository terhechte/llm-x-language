from task import TaskCheck
from base_executor import exec_check_common
from exec_cpp.cpp_utils import cpp_utils
from utils import TaskResult

def exec_check(task: TaskCheck, model: str, run: int) -> TaskResult:
    return exec_check_common(task, model, run, cpp_utils)