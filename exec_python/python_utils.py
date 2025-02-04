import os
import subprocess
import logging
import json
from typing import Tuple, Optional
from llm import request_openrouter
from utils import find_code_blocks_with_language, Result

TEMPLATE = "python_container"
TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "../../", TEMPLATE)
TEMPLATE_DEST = os.path.join(os.path.dirname(__file__), "../dojo", TEMPLATE)


def prepare_codebase(python_code: str) -> str:
    """
    Prepares the Python codebase by writing the code to main.py in the template directory.
    """
    # Write the Python code to main.py
    with open(os.path.join(TEMPLATE_DEST, "main.py"), "w", encoding="utf-8") as f:
        f.write(python_code)
    return TEMPLATE_DEST


def query_code(prompt: str, model: str) -> Optional[Tuple[str, str, int, int]]:
    """
    Queries the LLM for Python code based on the prompt.
    Returns a tuple of (code, response) or None if the query fails.
    """
    response, prompt_tokens, completion_tokens = request_openrouter(
        prompt, model, "Python"
    )
    logging.debug(response)
    logging.debug("--------------------------------")
    if not response:
        return None

    code_blocks = find_code_blocks_with_language(response)
    python_code = "\n".join(
        code for lang, code in code_blocks if lang.lower() in ["python", "py"]
    )
    logging.debug(python_code)
    return python_code, response, prompt_tokens, completion_tokens


def run_pylint_check(code_path: str) -> Result:
    """
    Runs pylint on the Python code to check for errors.
    Returns a Result object with success status and any errors found.
    """
    try:
        result = subprocess.run(
            [
                "poetry",
                "run",
                "pylint",
                "--output-format=json",
                os.path.join(code_path, "main.py"),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        errors = []
        if result.stdout:
            try:
                messages = json.loads(result.stdout)
                for msg in messages:
                    if msg["type"] in ["error", "fatal"]:
                        errors.append(
                            f"{msg['type'].upper()}: {msg['message']} (line {msg['line']})"
                        )
            except json.JSONDecodeError:
                errors.append("Failed to parse pylint output")

        return Result(success=len(errors) == 0, errors=errors)
    except subprocess.SubprocessError as e:
        logging.error("Error during pylint check: %s", e)
        return Result(success=False, errors=[str(e)])


def run_python_script(code_path: str) -> Result:
    """
    Runs the Python script and returns its output.
    Times out after 60 seconds.
    """
    try:
        result = subprocess.run(
            ["poetry", "run", "python", "main.py"],
            cwd=code_path,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )

        if result.stderr:
            logging.debug("Raw Err Output: %s", result.stderr)
            return Result(success=False, errors=[result.stderr])

        logging.debug("Raw Output: %s", result.stdout)
        return Result(success=True, errors=[result.stdout])

    except subprocess.TimeoutExpired:
        logging.error("Python script execution timed out after 60 seconds")
        return Result(success=False, errors=["Execution timed out after 60 seconds"])
    except subprocess.SubprocessError as e:
        logging.error("Error running Python script: %s", e)
        return Result(success=False, errors=[str(e)])
