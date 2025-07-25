from task import TaskContains
from base_executor import exec_contains_common
from exec_go.go_utils import go_utils
from utils import TaskResult


def exec_contains(task: TaskContains, model: str, run: int) -> TaskResult:
    """
    Execute a TaskContains for Go code.
    Returns a TaskResult containing the check results.
    """
    return exec_contains_common(task, model, run, go_utils)