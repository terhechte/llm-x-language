from task import TaskContains
from base_executor import exec_contains_common
from exec_rust.rust_utils import rust_utils
from utils import TaskResult


def exec_contains(task: TaskContains, model: str, run: int) -> TaskResult:
    """
    Execute a TaskContains for Rust code.
    Returns a TaskResult indicating if the contains check passed.
    """
    return exec_contains_common(task, model, run, rust_utils)