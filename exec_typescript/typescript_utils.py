import threading
from typing import Tuple, Any
from subprocess import Popen
import os
import logging
import subprocess
from llm import request_openrouter
from utils import find_code_blocks_with_language, Result

TEMPLATE = "typescript_container"
TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "../../", TEMPLATE)
TEMPLATE_DEST = os.path.join(os.path.dirname(__file__), "../dojo", TEMPLATE)


def prepare_codebase(typescript_code: str) -> str:
    """Write TypeScript code to index.ts and return the path."""
    with open(os.path.join(TEMPLATE_DEST, "src/index.ts"), "w", encoding="utf-8") as f:
        f.write(typescript_code)
    return TEMPLATE_DEST


def query_code(prompt: str, model: str) -> Tuple[str, str, int, int] | None:
    """Query the LLM for TypeScript code."""
    response, prompt_tokens, completion_tokens = request_openrouter(
        prompt, model, "TypeScript"
    )
    logging.debug(response)
    logging.debug("--------------------------------")
    if not response:
        return None

    # Extract and combine code blocks
    code_blocks = find_code_blocks_with_language(response)
    typescript_code = "\n".join(
        code for lang, code in code_blocks if lang.lower() in ["typescript", "ts"]
    )
    logging.debug(typescript_code)
    return typescript_code, response, prompt_tokens, completion_tokens


def run_tsc_check(code_path: str) -> Result:
    """Run TypeScript compiler check."""
    errors = []
    try:
        result = subprocess.run(
            ["pnpm", "run", "typecheck"],
            cwd=code_path,
            capture_output=True,
            check=False,
            text=True,
        )

        if result.stderr:
            errors.extend(result.stderr.splitlines())
        if result.stdout and "error" in result.stdout.lower():
            errors.extend(result.stdout.splitlines())

        logging.debug("Errors: %s", errors)
        logging.debug("Result: %s", result.returncode)

        return Result(success=result.returncode == 0, errors=errors)

    except subprocess.SubprocessError as e:
        logging.error("Error during tsc check: %s", e)
        return Result(success=False, errors=[str(e)])


def run_typescript_project(
    code_path: str,
) -> Tuple[threading.Thread, Popen[Any] | None]:
    """Run the TypeScript project in a separate thread."""
    process = None

    def run_target():
        nonlocal process
        try:
            process = Popen(
                ["pnpm", "dev"],
                cwd=code_path,
            )
        except subprocess.SubprocessError as e:
            logging.error("Error running TypeScript project: %s", e)

    thread = threading.Thread(target=run_target)
    thread.start()

    # Wait briefly to ensure process is created
    thread.join(0.2)

    return thread, process


def run_typescript_project_with_output(code_path: str) -> Result:
    """Run the TypeScript project and return its output."""
    try:
        result = subprocess.run(
            ["pnpm", "dev"],
            cwd=code_path,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )

        if result.stderr and (
            "error" in result.stderr.lower() or "failed" in result.stderr.lower()
        ):
            logging.debug("Raw Err Output: %s", result.stderr)
            return Result(success=False, errors=[result.stderr])

        logging.debug("Raw output: %s", result.stdout)
        # Remove lines starting with "> " from stdout
        filtered_output = "\n".join(
            line for line in result.stdout.splitlines() if not line.startswith("> ")
        )
        logging.debug("Filtered output: %s", filtered_output)
        return Result(success=True, errors=[filtered_output])

    except subprocess.TimeoutExpired:
        logging.error("TypeScript project execution timed out after 60 seconds")
        return Result(success=False, errors=["Execution timed out after 60 seconds"])
    except subprocess.SubprocessError as e:
        logging.error("Error running TypeScript project: %s", e)
        return Result(success=False, errors=[str(e)])
