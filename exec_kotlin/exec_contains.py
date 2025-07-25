from task import TaskContains
from base_executor import exec_contains_common
from exec_kotlin.kotlin_utils import kotlin_utils
from utils import TaskResult


def exec_contains(task: TaskContains, model: str, run: int) -> TaskResult:
    """
    Execute a TaskContains for Kotlin Native code.
    Returns a TaskResult containing the execution results.
    """
    return exec_contains_common(task, model, run, kotlin_utils)