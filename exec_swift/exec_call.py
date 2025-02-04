import logging
import json
from task import TaskCall
from utils import are_json_values_equal, TaskResult, are_string_values_equal
from exec_swift.swift_utils import (
    query_code,
    prepare_codebase,
    run_swift_check,
    run_swift_project_with_output,
)


def exec_call(task: TaskCall, model: str, run: int) -> TaskResult:
    """
    Execute a TaskCall for Swift code.
    Returns a TaskResult containing the execution results and relevant code/output.
    """
    try:
        r = query_code(task.prompt, model, matches_func=True)
    except (ValueError, RuntimeError, TimeoutError) as e:
        return TaskResult.error(run, [str(e)])
    logging.debug("Swift code: %s", r)
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

    # check if we have multiline input
    payload = f'#"{task.input_contents}"#'
    if "\n" in task.input_contents:
        payload = f'#"""\n{task.input_contents}\n"""#'

    # Add main function to call example
    swift_code += f"""

// Main entry point
print(example(input: {payload}))
"""

    code_path = prepare_codebase(swift_code)
    if not code_path:
        logging.error("Failed to prepare codebase")
        return TaskResult(
            run=run,
            success=False,
            errors=["Failed to prepare codebase"],
            response=response,
            code=swift_code,
            output="",
            expected_output=task.expected_output,
            tokens=(prompt_tokens, completion_tokens),
        )

    # Run swift build
    result = run_swift_check(code_path)
    if not result.success:
        logging.error("Failed to run swift build")
        return TaskResult(
            run=run,
            success=False,
            errors=["Failed to run swift build"] + result.errors,
            response=response,
            code=swift_code,
            output="",
            expected_output=task.expected_output,
            tokens=(prompt_tokens, completion_tokens),
        )

    output = run_swift_project_with_output(code_path)
    logging.debug("Output: %s", output)
    if not output.success:
        return TaskResult(
            run=run,
            success=False,
            errors=["Failed to run swift project"] + output.errors,
            response=response,
            code=swift_code,
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
            code=swift_code,
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
                code=swift_code,
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
                code=swift_code,
                output=output.errors[0],
                expected_output=json.dumps(task.expected_output),
                tokens=(prompt_tokens, completion_tokens),
            )
    else:
        return TaskResult(
            run=run,
            success=False,
            errors=["Invalid expected output type"],
            response=response,
            code=swift_code,
            output=output.errors[0],
            expected_output=str(task.expected_output),
            tokens=(prompt_tokens, completion_tokens),
        )
