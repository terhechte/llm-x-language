from task import TaskCall
from base_executor import exec_call_common
from exec_java.java_utils import java_utils
from utils import TaskResult

def exec_call(task: TaskCall, model: str, run: int) -> TaskResult:
    return exec_call_common(task, model, run, java_utils)