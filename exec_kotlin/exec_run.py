from task import TaskRun
from base_executor import exec_run_common
from exec_kotlin.kotlin_utils import kotlin_utils
from utils import TaskResult


def exec_run(task: TaskRun, model: str, run: int) -> TaskResult:
    """
    Execute a TaskRun for Kotlin Native code (typically for HTTP server tasks).
    Returns a TaskResult containing the execution results.
    """
    return exec_run_common(task, model, run, kotlin_utils)