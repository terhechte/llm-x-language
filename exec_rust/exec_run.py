from task import TaskRun
from base_executor import exec_run_common
from exec_rust.rust_utils import rust_utils
from utils import TaskResult


def exec_run(task: TaskRun, model: str, run: int) -> TaskResult:
    """
    Execute a TaskRun for Rust code.
    Returns a TaskResult containing the execution results and relevant code/output.
    """
    return exec_run_common(task, model, run, rust_utils)