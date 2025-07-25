from task import TaskCall
from base_executor import exec_call_common
from exec_kotlin.kotlin_utils import kotlin_utils
from utils import TaskResult


def exec_call(task: TaskCall, model: str, run: int) -> TaskResult:
    """
    Execute a TaskCall for Kotlin Native code.
    Returns a TaskResult containing the execution results.
    """
    import time
    print(f"[DEBUG {time.time():.3f}] exec_kotlin/exec_call: Starting Kotlin task execution")
    print(f"[DEBUG {time.time():.3f}] exec_kotlin/exec_call: Task input: {task.input_contents[:100]}...")
    result = exec_call_common(task, model, run, kotlin_utils)
    print(f"[DEBUG {time.time():.3f}] exec_kotlin/exec_call: Task completed, success: {result.result.success}")
    return result