import threading
from typing import Tuple, Any
from subprocess import Popen
import os
import logging
import subprocess
from llm import request
from utils import find_code_blocks_with_language, Result, wait_for_server_ready, ProcessManager

TEMPLATE = "swift_container"
TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "../../", TEMPLATE)
TEMPLATE_DEST = os.path.join(os.path.dirname(__file__), "../dojo", TEMPLATE)


def prepare_codebase(swift_code: str) -> str:
    """Prepare the Swift codebase by writing the code to main.swift"""
    try:
        with open(
            os.path.join(TEMPLATE_DEST, "Sources/main.swift"), "w", encoding="utf-8"
        ) as f:
            f.write(swift_code)
        return TEMPLATE_DEST
    except IOError as e:
        logging.error(f"Failed to write Swift code to Sources/main.swift: {e}")
        raise


def query_code(
    prompt: str, model: str, matches_func: bool = False
) -> Tuple[str, str, int, int] | None:
    """Query the model for Swift code and extract it from the response"""
    response, prompt_tokens, completion_tokens = request(prompt, model, "Swift")
    logging.debug(response)
    if not response:
        return None

    code_blocks = find_code_blocks_with_language(response)
    if matches_func:
        code_blocks = [b for b in code_blocks if b[1].find("func example") != -1]
    swift_code = "\n".join(
        code for lang, code in code_blocks if lang.lower() in ["swift"]
    )
    if swift_code.find("import Foundation") == -1:
        swift_code = "import Foundation\n\n" + swift_code
    if swift_code.find("@main\n") > -1:
        swift_code = swift_code.replace("@main\n", "\n")
    logging.debug(swift_code)
    return swift_code, response, prompt_tokens, completion_tokens


def run_swift_check(code_path: str) -> Result:
    """Run swift build to check for compilation errors"""
    errors = []
    try:
        result = subprocess.run(
            ["swift", "build"],
            cwd=code_path,
            capture_output=True,
            text=True,
            check=False,
        )

        lines = []
        contains_error = False
        for line in result.stdout.split("\n"):
            lines.append(line.strip())
            if line.strip() and "error:" in line and ".swift" in line:
                contains_error = True
        if contains_error:
            errors.append("\n".join(lines))
        if result.stderr:
            for line in result.stderr.split("\n"):
                if line.strip() and "error:" in line:
                    errors.append(line.strip())

        return Result(success=result.returncode == 0, errors=errors)
    except subprocess.SubprocessError as e:
        logging.error("Error during swift build: %s", e)
        return Result(success=False, errors=[str(e)])


def run_swift_project(code_path: str, url: str = None) -> Tuple[threading.Thread, ProcessManager, bool]:
    """Run the Swift project in a separate thread with proper synchronization"""
    process_manager = ProcessManager()

    def run_target():
        process_manager.start_process(
            ["swift", "run"],
            cwd=code_path,
        )

    thread = threading.Thread(target=run_target)
    thread.start()

    # Wait for process to start
    if not process_manager.wait_for_start():
        return thread, process_manager, False

    # Wait for server to be ready if URL provided
    is_ready = True
    if url:
        is_ready = wait_for_server_ready(url)

    return thread, process_manager, is_ready


def run_swift_project_with_output(code_path: str) -> Result:
    """Run the Swift project and return its output"""
    try:
        result = subprocess.run(
            ["swift", "run"],
            cwd=code_path,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )

        if result.stderr and "error:" in result.stderr:
            logging.debug("Raw Err Output: %s", result.stderr)
            return Result(success=False, errors=[result.stderr])

        logging.debug("Raw Output: %s", result.stdout)
        return Result(success=True, errors=[], output=result.stdout)

    except subprocess.TimeoutExpired:
        logging.error("Swift project execution timed out after 60 seconds")
        return Result(success=False, errors=["Execution timed out after 60 seconds"])
    except subprocess.SubprocessError as e:
        logging.error("Error running Swift project: %s", e)
        return Result(success=False, errors=[str(e)])
