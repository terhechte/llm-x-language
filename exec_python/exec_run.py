import threading
import subprocess
import json
import logging
from task import TaskRun
import requests
from utils import are_json_values_equal, TaskResult
from exec_python.python_utils import (
    query_code,
    prepare_codebase,
    run_pylint_check,
)


def exec_run(task: TaskRun, model: str, run: int) -> TaskResult:
    """
    Execute a TaskRun for Python code.
    Returns a TaskResult containing the execution results and relevant code/output.
    """
    process = None  # Store process reference at function scope
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
    python_code, response, prompt_tokens, completion_tokens = r

    code_path = prepare_codebase(python_code)
    if not code_path:
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
        return TaskResult(
            run=run,
            success=False,
            errors=result.errors,
            response=response,
            code=python_code,
            output="",
            expected_output=task.expected_output,
            tokens=(prompt_tokens, completion_tokens),
        )

    # Run the Python script in a separate thread
    def run_target():
        nonlocal process  # Access the outer process variable
        try:
            process = subprocess.Popen(
                ["poetry", "run", "python", "main.py"],
                cwd=code_path,
            )
        except subprocess.SubprocessError as e:
            logging.error("Error running Python script: %s", e)

    thread = threading.Thread(target=run_target)
    thread.start()
    thread.join(0.2)  # Give it a moment to start

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
            code=python_code,
            output="",
            expected_output=task.expected_output,
            tokens=(prompt_tokens, completion_tokens),
        )
    finally:
        # Ensure subprocess is terminated
        if process:
            process.terminate()  # Send SIGTERM
            try:
                process.wait(timeout=5)  # Wait up to 5 seconds for graceful shutdown
            except subprocess.TimeoutExpired:
                process.kill()  # Force kill if process doesn't terminate gracefully
                process.wait()  # Wait for the process to be killed

    # Compare the response to the expected output
    if isinstance(task.expected_output, str):
        response_text = http_response.text
        return TaskResult(
            run=run,
            success=response_text.strip() == task.expected_output.strip(),
            errors=[],
            response=response,
            code=python_code,
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
            code=python_code,
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
            code=python_code,
            output="",
            expected_output=str(task.expected_output),
            tokens=(prompt_tokens, completion_tokens),
        )
