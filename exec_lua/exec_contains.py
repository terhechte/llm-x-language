import json
from task import TaskContains
from utils import TaskResult, check_contains_matches
from exec_lua.lua_utils import query_code


def exec_contains(task: TaskContains, model: str, run: int) -> TaskResult:
    """
    Execute a TaskContains for Lua code.
    Returns a TaskResult indicating if the contains check passed.
    """
    try:
        r = query_code(task.prompt, model)
    except Exception as e:
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
    response, _, prompt_tokens, completion_tokens = r

    valid_position_found = check_contains_matches(response, task.matches, task.mode)

    return TaskResult(
        run=run,
        success=valid_position_found,
        errors=[] if valid_position_found else ["Contains check failed"],
        response=response,
        code="",
        output="",
        expected_output=json.dumps(
            {
                "matches": [
                    {
                        "contains": match.contains,
                        "before": match.before,
                        "after": match.after,
                    }
                    for match in task.matches
                ],
                "mode": task.mode,
            }
        ),
        tokens=(prompt_tokens, completion_tokens),
    )
