from task import TaskCheck
from base_executor import exec_check_common
from exec_kotlin.kotlin_utils import kotlin_utils
from utils import TaskResult


def exec_check(task: TaskCheck, model: str, run: int) -> TaskResult:
    """
    Execute a TaskCheck for Kotlin Native code validation.
    Returns a TaskResult containing the execution results.
    """
    return exec_check_common(task, model, run, kotlin_utils)