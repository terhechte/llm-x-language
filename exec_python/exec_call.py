import json
import logging
from task import TaskCall
from utils import are_string_values_equal, are_json_values_equal, TaskResult
from exec_python.python_utils import (
    query_code,
    prepare_codebase,
    run_pylint_check,
    run_python_script,
)


def exec_call(task: TaskCall, model: str, run: int) -> TaskResult:
    """
    Execute a TaskCall for Python code.
    Returns a TaskResult containing the execution results and relevant code/output.
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
    python_code, response, prompt_tokens, completion_tokens = r

    # Wrap the code to handle input
    python_code = f"""
{python_code.strip()}

if __name__ == "__main__":
    import sys
    print(example(r'''{task.input_contents}'''))
"""

    code_path = prepare_codebase(python_code)
    if not code_path:
        logging.error("Failed to prepare codebase")
        return TaskResult(
            run=run,
            success=False,
            errors=["Failed to prepare codebase"],
            response=response,
            code=python_code,
            output="",
            expected_output=task.expected_output,
            tokens=(prompt_tokens, completion_tokens),
        )

    # Run pylint check
    result = run_pylint_check(code_path)
    if not result.success:
        logging.error("Failed pylint check")
        return TaskResult(
            run=run,
            success=False,
            errors=["Failed pylint check"] + result.errors,
            response=response,
            code=python_code,
            output="",
            expected_output=task.expected_output,
            tokens=(prompt_tokens, completion_tokens),
        )

    output = run_python_script(code_path)
    logging.debug("Output: %s", output)
    if not output.success:
        return TaskResult(
            run=run,
            success=False,
            errors=["Failed to run python script"] + output.errors,
            response=response,
            code=python_code,
            output=output.errors[0],
            expected_output=task.expected_output,
            tokens=(prompt_tokens, completion_tokens),
        )

    if isinstance(task.expected_output, str):
        return TaskResult(
            run=run,
            success=are_string_values_equal(
                output.errors[0], task.expected_output, task.lowercase
            ),
            errors=[],
            response=response,
            code=python_code,
            output=output.errors[0],
            expected_output=task.expected_output,
            tokens=(prompt_tokens, completion_tokens),
        )
    elif isinstance(task.expected_output, (dict, list)):
        try:
            output_json = json.loads(output.errors[0])
            return TaskResult(
                run=run,
                success=are_json_values_equal(output_json, task.expected_output),
                errors=[],
                response=response,
                code=python_code,
                output=json.dumps(output_json),
                expected_output=json.dumps(task.expected_output),
                tokens=(prompt_tokens, completion_tokens),
            )
        except json.JSONDecodeError:
            logging.error("Output string is not valid JSON")
            logging.debug("Output: %s", output)
            return TaskResult(
                run=run,
                success=False,
                errors=["Output string is not valid JSON"],
                response=response,
                code=python_code,
                output=output.errors[0] if output.errors else "",
                expected_output=json.dumps(task.expected_output),
                tokens=(prompt_tokens, completion_tokens),
            )
    else:
        return TaskResult(
            run=run,
            success=False,
            errors=["Invalid expected output type"],
            response=response,
            code=python_code,
            output=output.errors[0] if output.errors else "",
            expected_output=str(task.expected_output),
            tokens=(prompt_tokens, completion_tokens),
        )
