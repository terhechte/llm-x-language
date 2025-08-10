from task import TaskContains
from base_executor import exec_contains_common
from exec_scala.scala_utils import scala_utils
from utils import TaskResult

def exec_contains(task: TaskContains, model: str, run: int) -> TaskResult:
    return exec_contains_common(task, model, run, scala_utils)