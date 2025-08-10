from task import TaskRun
from base_executor import exec_run_common
from exec_cpp.cpp_utils import cpp_utils
from utils import TaskResult

def exec_run(task: TaskRun, model: str, run: int) -> TaskResult:
    return exec_run_common(task, model, run, cpp_utils)