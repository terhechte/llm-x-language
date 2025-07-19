from task import TaskRun
from base_executor import exec_run_common
from exec_php.php_utils import php_utils
from utils import TaskResult


def exec_run(task: TaskRun, model: str, run: int) -> TaskResult:
    """
    Execute a TaskRun for PHP code.
    Returns a TaskResult containing the execution results and relevant code/output.
    """
    return exec_run_common(task, model, run, php_utils)