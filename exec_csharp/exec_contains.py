from task import TaskContains
from base_executor import exec_contains_common
from exec_csharp.csharp_utils import csharp_utils
from utils import TaskResult


def exec_contains(task: TaskContains, model: str, run: int) -> TaskResult:
    """
    Execute a TaskContains for C# code.
    Returns a TaskResult containing whether the response contains expected matches.
    """
    return exec_contains_common(task, model, run, csharp_utils)