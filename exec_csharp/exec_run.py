from task import TaskRun
from base_executor import exec_run_common
from exec_csharp.csharp_utils import csharp_utils
from utils import TaskResult


def exec_run(task: TaskRun, model: str, run: int) -> TaskResult:
    """
    Execute a TaskRun for C# code.
    Returns a TaskResult containing the HTTP server execution results.
    """
    return exec_run_common(task, model, run, csharp_utils)