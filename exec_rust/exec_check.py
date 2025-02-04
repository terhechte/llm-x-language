from task import TaskCheck
from exec_rust.rust_utils import prepare_codebase, query_code, run_cargo_check
from utils import TaskResult


def exec_check(task: TaskCheck, model: str, run: int) -> TaskResult:
    """
    Execute a TaskCheck for Rust code.
    Returns a tuple of (Result, queried_code) where Result indicates success/failure
    and queried_code contains the generated Rust code (or None if query failed).
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
    rust_code, response, prompt_tokens, completion_tokens = r

    code_path = prepare_codebase(rust_code)
    if not code_path:
        return TaskResult(
            run=run,
            success=False,
            errors=["Failed to prepare codebase"],
            response=response,
            code=rust_code,
            output="",
            expected_output="",
            tokens=(prompt_tokens, completion_tokens),
        )

    # Run cargo check
    result = run_cargo_check(code_path)
    return TaskResult(
        run=run,
        success=result.success,
        errors=result.errors,
        response=response,
        code=rust_code,
        output="",
        expected_output="",
        tokens=(prompt_tokens, completion_tokens),
    )
