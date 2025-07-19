from task import TaskCall
from base_executor import exec_call_common
from exec_php.php_utils import php_utils
from utils import TaskResult


def exec_call(task: TaskCall, model: str, run: int) -> TaskResult:
    """
    Execute a TaskCall for PHP code.
    Returns a TaskResult containing the execution results and relevant code/output.
    """
    return exec_call_common(task, model, run, php_utils)