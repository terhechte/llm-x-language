from task import TaskContains
from base_executor import exec_contains_common
from exec_php.php_utils import php_utils
from utils import TaskResult


def exec_contains(task: TaskContains, model: str, run: int) -> TaskResult:
    """
    Execute a TaskContains for PHP code.
    Returns a TaskResult indicating if the contains check passed.
    """
    return exec_contains_common(task, model, run, php_utils)