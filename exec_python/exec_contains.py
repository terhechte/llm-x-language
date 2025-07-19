from task import TaskContains
from base_executor import exec_contains_common
from exec_python.python_utils import python_utils
from utils import TaskResult


def exec_contains(task: TaskContains, model: str, run: int) -> TaskResult:
    """
    Execute a TaskContains for Python code.
    Returns a TaskResult indicating if the contains check passed.
    """
    return exec_contains_common(task, model, run, python_utils)
