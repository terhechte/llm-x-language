from task import TaskCheck
from base_executor import exec_check_common
from exec_rust.rust_utils import rust_utils
from utils import TaskResult


def exec_check(task: TaskCheck, model: str, run: int) -> TaskResult:
    """
    Execute a TaskCheck for Rust code.
    Returns a TaskResult containing success/failure status and any errors.
    """
    return exec_check_common(task, model, run, rust_utils)