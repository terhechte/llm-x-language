from task import TaskCheck
from exec_swift.swift_utils import prepare_codebase, query_code, run_swift_check
from utils import TaskResult


def exec_check(task: TaskCheck, model: str, run: int) -> TaskResult:
    """
    Execute a TaskCheck for Swift code.
    Returns a TaskResult indicating success/failure and containing any errors.
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
    swift_code, response, prompt_tokens, completion_tokens = r

    code_path = prepare_codebase(swift_code)
    if not code_path:
        return TaskResult(
            run=run,
            success=False,
            errors=["Failed to prepare codebase"],
            response=response,
            code=swift_code,
            output="",
            expected_output="",
            tokens=(prompt_tokens, completion_tokens),
        )

    # Run swift build
    result = run_swift_check(code_path)
    return TaskResult(
        run=run,
        success=result.success,
        errors=result.errors,
        response=response,
        code=swift_code,
        output="",
        expected_output="",
        tokens=(prompt_tokens, completion_tokens),
    )
