from task import TaskCheck
from base_executor import exec_check_common
from exec_go.go_utils import go_utils
from utils import TaskResult


def exec_check(task: TaskCheck, model: str, run: int) -> TaskResult:
    """
    Execute a TaskCheck for Go code.
    Returns a TaskResult containing the validation results.
    """
    return exec_check_common(task, model, run, go_utils)