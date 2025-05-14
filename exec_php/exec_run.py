import threading
import subprocess
import requests
import json
import os
from task import TaskRun
from utils import TaskResult, are_json_values_equal
from exec_php.php_utils import prepare_codebase, query_code, run_php_check
import logging
from time import sleep


def exec_run(task: TaskRun, model: str, run: int) -> TaskResult:
    """
    Execute PHP code and return the results
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
    php_code, response, prompt_tokens, completion_tokens = r

    code_path = prepare_codebase(php_code)
    result = run_php_check(code_path)
    if not result.success:
        return TaskResult(
            run=run,
            success=False,
            errors=["Failed PHP syntax check"] + result.errors,
            response=response,
            code=php_code,
            output="",
            expected_output=task.expected_output,
            tokens=(prompt_tokens, completion_tokens),
        )

    process = None

    def run_script():
        nonlocal process
        process = subprocess.Popen(
            ["php", os.path.join(code_path, "main.php")],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        process.communicate()

    thread = threading.Thread(target=run_script)
    thread.start()

    sleep(0.5)
    http_response = None
    error = None
    try:
        http_response = requests.get(task.request, timeout=10)
        http_response.raise_for_status()
    except requests.RequestException as e:
        logging.error("Error during HTTP request: %s", e)
        error = str(e)

    # Wait for the thread to finish, but don't block forever
    thread.join(timeout=2)
    if thread.is_alive() and process:
        process.terminate()
        thread.join(timeout=1)
    elif process:
        process.terminate()

    if error:
        return TaskResult(
            run=run,
            success=False,
            errors=["Failed to make HTTP request", error],
            response=response,
            code=php_code,
            output="",
            expected_output=task.expected_output,
            tokens=(prompt_tokens, completion_tokens),
        )
    if not http_response:
        return TaskResult(
            run=run,
            success=False,
            errors=["Failed to make HTTP request. No Response"],
            response=response,
            code=php_code,
            output="",
            expected_output=task.expected_output,
            tokens=(prompt_tokens, completion_tokens),
        )

    # Compare the HTTP response to the expected output
    if isinstance(task.expected_output, str):
        response_text = http_response.text
        return TaskResult(
            run=run,
            success=response_text.strip() == str(task.expected_output).strip(),
            errors=[],
            response=response,
            code=php_code,
            output=response_text,
            expected_output=task.expected_output,
            tokens=(prompt_tokens, completion_tokens),
        )
    elif isinstance(task.expected_output, dict):
        try:
            response_json = http_response.json()
        except:
            return TaskResult(
                run=run,
                success=False,
                errors=["Invalid JSON response"],
                response=response,
                code=php_code,
                output="",
                expected_output=task.expected_output,
                tokens=(prompt_tokens, completion_tokens),
            )

        return TaskResult(
            run=run,
            success=are_json_values_equal(response_json, task.expected_output),
            errors=[],
            response=response,
            code=php_code,
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
            code=php_code,
            output="",
            expected_output=str(task.expected_output),
            tokens=(prompt_tokens, completion_tokens),
        )
