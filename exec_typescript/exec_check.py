from task import TaskCheck
from exec_typescript.typescript_utils import prepare_codebase, query_code, run_tsc_check
from utils import TaskResult


def exec_check(task: TaskCheck, model: str, run: int) -> TaskResult:
    """
    Execute a TaskCheck for TypeScript code.
    Returns a TaskResult containing the compilation check results.
    """
    try:
        r = query_code(task.prompt, model)
    except (ValueError, RuntimeError, TimeoutError) as e:
        return TaskResult.error(run, [str(e)])
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
    typescript_code, response, prompt_tokens, completion_tokens = r

    code_path = prepare_codebase(typescript_code)
    if not code_path:
        return TaskResult(
            run=run,
            success=False,
            errors=["Failed to prepare codebase"],
            response=response,
            code=typescript_code,
            output="",
            expected_output="",
            tokens=(prompt_tokens, completion_tokens),
        )

    # Run TypeScript check
    result = run_tsc_check(code_path)
    return TaskResult(
        run=run,
        success=result.success,
        errors=result.errors,
        response=response,
        code=typescript_code,
        output="",
        expected_output="",
        tokens=(prompt_tokens, completion_tokens),
    )
