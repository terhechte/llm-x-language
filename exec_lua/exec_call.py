import json
import logging
from task import TaskCall
from utils import are_string_values_equal, are_json_values_equal, TaskResult
from exec_lua.lua_utils import (
    query_code,
    prepare_codebase,
    run_lua_check,
    run_lua_script,
)


def exec_call(task: TaskCall, model: str, run: int) -> TaskResult:
    """
    Execute a TaskCall for Lua code.
    Runs the code and compares the output with the expected output.
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
            expected_output=task.expected_output,
            tokens=(0, 0),
        )
    lua_code, response, prompt_tokens, completion_tokens = r

    code_path = prepare_codebase(lua_code)
    if not code_path:
        logging.error("Failed to prepare codebase")
        return TaskResult(
            run=run,
            success=False,
            errors=["Failed to prepare codebase"],
            response=response,
            code=lua_code,
            output="",
            expected_output=task.expected_output,
            tokens=(prompt_tokens, completion_tokens),
        )

    # Run Lua syntax check
    result = run_lua_check(code_path)
    if not result.success:
        logging.error("Failed Lua syntax check")
        return TaskResult(
            run=run,
            success=False,
            errors=["Failed Lua syntax check"] + result.errors,
            response=response,
            code=lua_code,
            output="",
            expected_output=task.expected_output,
            tokens=(prompt_tokens, completion_tokens),
        )

    output = run_lua_script(code_path)
    logging.debug("Output: %s", output)
    if not output.success:
        return TaskResult(
            run=run,
            success=False,
            errors=["Failed to run Lua script"] + output.errors,
            response=response,
            code=lua_code,
            output="",
            expected_output=task.expected_output,
            tokens=(prompt_tokens, completion_tokens),
        )

    if isinstance(task.expected_output, str):
        return TaskResult(
            run=run,
            success=are_string_values_equal(
                output.output if output.output is not None else "", task.expected_output, task.lowercase
            ),
            errors=[],
            response=response,
            code=lua_code,
            output=output.output if output.output is not None else "",
            expected_output=task.expected_output,
            tokens=(prompt_tokens, completion_tokens),
        )
    elif isinstance(task.expected_output, (dict, list)):
        try:
            output_json = json.loads(output.output if output.output is not None else "{}")
            return TaskResult(
                run=run,
                success=are_json_values_equal(output_json, task.expected_output),
                errors=[],
                response=response,
                code=lua_code,
                output=json.dumps(output_json),
                expected_output=json.dumps(task.expected_output),
                tokens=(prompt_tokens, completion_tokens),
            )
        except json.JSONDecodeError:
            return TaskResult(
                run=run,
                success=False,
                errors=["Output is not valid JSON"],
                response=response,
                code=lua_code,
                output=output.output if output.output is not None else "",
                expected_output=task.expected_output,
                tokens=(prompt_tokens, completion_tokens),
            )
    else:
        return TaskResult(
            run=run,
            success=False,
            errors=["Invalid expected output type"],
            response=response,
            code=lua_code,
            output=output.output if output.output is not None else "",
            expected_output=str(task.expected_output),
            tokens=(prompt_tokens, completion_tokens),
        )
