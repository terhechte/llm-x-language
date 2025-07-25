from task import TaskCall
from base_executor import exec_call_common
from exec_kotlin.kotlin_utils import kotlin_utils
from utils import TaskResult


def exec_call(task: TaskCall, model: str, run: int) -> TaskResult:
    """
    Execute a TaskCall for Kotlin Native code.
    Returns a TaskResult containing the execution results.
    """
    return exec_call_common(task, model, run, kotlin_utils)