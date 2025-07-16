from task import TaskCheck
from exec_lua.lua_utils import prepare_codebase, query_code, run_lua_check
from utils import TaskResult


def exec_check(task: TaskCheck, model: str, run: int) -> TaskResult:
    """
    Execute a TaskCheck for Lua code.
    Returns a TaskResult containing success/failure status and any errors.
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
    lua_code, response, prompt_tokens, completion_tokens = r

    code_path = prepare_codebase(lua_code)
    if not code_path:
        return TaskResult(
            run=run,
            success=False,
            errors=["Failed to prepare codebase"],
            response=response,
            code=lua_code,
            output="",
            expected_output="",
            tokens=(prompt_tokens, completion_tokens),
        )

    # Run lua syntax check
    result = run_lua_check(code_path)
    return TaskResult(
        run=run,
        success=result.success,
        errors=result.errors,
        response=response,
        code=lua_code,
        output="",
        expected_output="",
        tokens=(prompt_tokens, completion_tokens),
    )
