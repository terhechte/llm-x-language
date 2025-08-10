from task import TaskCall
from base_executor import exec_call_common
from exec_csharp.csharp_utils import csharp_utils
from utils import TaskResult


def exec_call(task: TaskCall, model: str, run: int) -> TaskResult:
    """
    Execute a TaskCall for C# code.
    Returns a TaskResult containing the execution results and relevant code/output.
    """
    return exec_call_common(task, model, run, csharp_utils)