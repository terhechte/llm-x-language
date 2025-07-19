from task import TaskCheck
from base_executor import exec_check_common
from exec_typescript.typescript_utils import typescript_utils
from utils import TaskResult


def exec_check(task: TaskCheck, model: str, run: int) -> TaskResult:
    """
    Execute a TaskCheck for TypeScript code.
    Returns a TaskResult containing success/failure status and any errors.
    """
    return exec_check_common(task, model, run, typescript_utils)