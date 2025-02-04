from task import TaskRun
import requests
from utils import are_json_values_equal
import logging
from exec_swift.swift_utils import (
    query_code,
    prepare_codebase,
    run_swift_check,
    run_swift_project,
)
from utils import TaskResult
import json


def exec_run(task: TaskRun, model: str, run: int) -> TaskResult:
    """
    Execute a TaskRun for Swift code.
    Returns a TaskResult containing the execution results and relevant code/output.
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
            expected_output=task.expected_output,
            tokens=(prompt_tokens, completion_tokens),
        )

    # Run swift check
    result = run_swift_check(code_path)
    if not result.success:
        return TaskResult(
            run=run,
            success=False,
            errors=result.errors,
            response=response,
            code=swift_code,
            output="",
            expected_output=task.expected_output,
            tokens=(prompt_tokens, completion_tokens),
        )

    thread, process = run_swift_project(code_path)
    if not thread or not process:
        return TaskResult(
            run=run,
            success=False,
            errors=["Failed to run swift project"],
            response=response,
            code=swift_code,
            output="",
            expected_output=task.expected_output,
            tokens=(prompt_tokens, completion_tokens),
        )

    # Make HTTP request to the specified URL
    try:
        http_response = requests.get(task.request, timeout=300)
        http_response.raise_for_status()
    except requests.RequestException as e:
        logging.error("Error during HTTP request: %s", e)
        return TaskResult(
            run=run,
            success=False,
            errors=["Failed to make HTTP request"],
            response=response,
            code=swift_code,
            output="",
            expected_output=task.expected_output,
            tokens=(prompt_tokens, completion_tokens),
        )

    thread.join()
    process.terminate()

    # Compare the JSON response to the expected output
    if isinstance(task.expected_output, str):
        response_text = http_response.text
        return TaskResult(
            run=run,
            success=response_text.strip() == task.expected_output.strip(),
            errors=[],
            response=response,
            code=swift_code,
            output=response_text,
            expected_output=task.expected_output,
            tokens=(prompt_tokens, completion_tokens),
        )
    elif isinstance(task.expected_output, dict):
        response_json = http_response.json()
        return TaskResult(
            run=run,
            success=are_json_values_equal(response_json, task.expected_output),
            errors=[],
            response=response,
            code=swift_code,
            output=json.dumps(response_json),
            expected_output=task.expected_output,
            tokens=(prompt_tokens, completion_tokens),
        )
    else:
        return TaskResult(
            run=run,
            success=False,
            errors=["Invalid expected output type"],
            response=response,
            code=swift_code,
            output="",
            expected_output=str(task.expected_output),
            tokens=(prompt_tokens, completion_tokens),
        )
