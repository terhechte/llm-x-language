from task import TaskContains
from llm import request
from utils import TaskResult, check_contains_matches
import json
import requests


def exec_contains(task: TaskContains, model: str, run: int) -> TaskResult:
    """
    Execute a TaskContains for TypeScript code.
    Returns a TaskResult indicating if the required patterns were found in the code.
    """
    try:
        response, prompt_tokens, completion_tokens = request(
            task.prompt, model, "TypeScript"
        )
    except (requests.RequestException, ValueError) as e:
        return TaskResult.error(run, [str(e)])
    if not response:
        return TaskResult(
            run=run,
            success=False,
            errors=["Failed to query code"],
            response="",
            code="",
            output="",
            expected_output="",
            tokens=(prompt_tokens, completion_tokens),
        )

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
