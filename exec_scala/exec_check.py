from task import TaskCheck
from base_executor import exec_check_common
from exec_scala.scala_utils import scala_utils
from utils import TaskResult

def exec_check(task: TaskCheck, model: str, run: int) -> TaskResult:
    return exec_check_common(task, model, run, scala_utils)