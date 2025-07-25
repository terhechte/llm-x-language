from task import TaskCall
from base_executor import exec_call_common
from exec_go.go_utils import go_utils
from utils import TaskResult


def exec_call(task: TaskCall, model: str, run: int) -> TaskResult:
    """
    Execute a TaskCall for Go code.
    Returns a TaskResult containing the execution results and relevant code/output.
    """
    return exec_call_common(task, model, run, go_utils)