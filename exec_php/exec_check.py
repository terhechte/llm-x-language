from task import TaskCheck
from exec_php.php_utils import prepare_codebase, query_code, run_php_check
from utils import TaskResult
from utils import are_json_values_equal, are_string_values_equal, TaskResult
from exec_php.php_utils import prepare_codebase, query_code, run_php_check, run_php_script
import logging


def exec_check(task: TaskCheck, model: str, run: int) -> TaskResult:
    """
    Check PHP code for syntax errors
    """
    try:
        r = query_code(task.prompt, model)
    except (ValueError, RuntimeError, TimeoutError) as e:
        return TaskResult.error(run, [str(e)])
    logging.debug("Python code: %s", r)
    if not r:
        return TaskResult(
            run=run,
            success=False,
            errors=["Failed to query code"],
            response="",
            code="",
            output="",
            expected_output="",
            tokens=(0, 0),
        )
    php_code, response, prompt_tokens, completion_tokens = r

    # Prepare the codebase
    code_path = prepare_codebase(php_code)
    if not code_path:
        logging.error("Failed to prepare codebase")
        return TaskResult(
            run=run,
            success=False,
            errors=["Failed to prepare codebase"],
            response=response,
            code=php_code,
            output="",
            expected_output="",
            tokens=(prompt_tokens, completion_tokens),
        )
    # Run PHP syntax check
    result = run_php_check(code_path)
    return TaskResult(
        run=run,
        success=result.success,
        errors=result.errors,
        response=response,
        code=php_code,
        output="",
        expected_output="",
        tokens=(prompt_tokens, completion_tokens),
    )