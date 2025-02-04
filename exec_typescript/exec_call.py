import logging
import json
from task import TaskCall
from utils import are_json_values_equal, TaskResult, are_string_values_equal
from exec_typescript.typescript_utils import (
    query_code,
    prepare_codebase,
    run_tsc_check,
    run_typescript_project_with_output,
)


def exec_call(task: TaskCall, model: str, run: int) -> TaskResult:
    """
    Execute a TaskCall for TypeScript code.
    Returns a TaskResult containing the execution results and relevant code/output.
    """
    try:
        r = query_code(task.prompt, model)
    except (ValueError, RuntimeError, TimeoutError) as e:
        return TaskResult.error(run, [str(e)])
    logging.debug("TypeScript code: %s", r)
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

    # Wrap the code in a function that handles the input
    if typescript_code.find("function example") == -1:
        return TaskResult(
            run=run,
            success=False,
            errors=["No example function found in generated code"],
            response=response,
            code=typescript_code,
            output="",
            expected_output=task.expected_output,
            tokens=(prompt_tokens, completion_tokens),
        )

    escaped_code = task.input_contents.replace("`", "\\`")
    # Add the execution code
    await_exp = ""
    if typescript_code.find("async function") != -1:
        await_exp = "await "
    typescript_code += f"""
// Execute the example function
const result = {await_exp}example(`{escaped_code}`);
console.log(result);
"""

    code_path = prepare_codebase(typescript_code)
    if not code_path:
        logging.error("Failed to prepare codebase")
        return TaskResult(
            run=run,
            success=False,
            errors=["Failed to prepare codebase"],
            response=response,
            code=typescript_code,
            output="",
            expected_output=task.expected_output,
            tokens=(prompt_tokens, completion_tokens),
        )

    # Run TypeScript check
    result = run_tsc_check(code_path)
    if not result.success:
        logging.error("Failed to run TypeScript check")
        return TaskResult(
            run=run,
            success=False,
            errors=["Failed to run TypeScript check"] + result.errors,
            response=response,
            code=typescript_code,
            output="",
            expected_output=task.expected_output,
            tokens=(prompt_tokens, completion_tokens),
        )

    output = run_typescript_project_with_output(code_path)
    logging.debug("Output: %s", output)
    if not output.success:
        return TaskResult(
            run=run,
            success=False,
            errors=["Failed to run TypeScript project"] + output.errors,
            response=response,
            code=typescript_code,
            output=output.errors[0] if output.errors else "",
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
            code=typescript_code,
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
                code=typescript_code,
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
                code=typescript_code,
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
            code=typescript_code,
            output=output.errors[0] if output.errors else "",
            expected_output=str(task.expected_output),
            tokens=(prompt_tokens, completion_tokens),
        )
