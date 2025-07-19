from task import TaskRun
from base_executor import exec_run_common
from exec_python.python_utils import python_utils
from utils import TaskResult


def exec_run(task: TaskRun, model: str, run: int) -> TaskResult:
    """
    Execute a TaskRun for Python code.
    Returns a TaskResult containing the execution results and relevant code/output.
    """
    return exec_run_common(task, model, run, python_utils)