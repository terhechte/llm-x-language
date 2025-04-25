import threading
from typing import Tuple, Any
from subprocess import Popen
import os
import re
import logging
import subprocess
import json
from llm import request
from utils import find_code_blocks_with_language, Result

TEMPLATE = "rust_container"
TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "../../", TEMPLATE)
TEMPLATE_DEST = os.path.join(os.path.dirname(__file__), "../dojo", TEMPLATE)


def prepare_codebase(rust_code: str) -> str:
    # if os.path.exists(TEMPLATE_DEST):
    #    shutil.rmtree(TEMPLATE_DEST)
    # shutil.copytree(TEMPLATE_PATH, TEMPLATE_DEST)

    # Write the Rust code to main.rs
    with open(os.path.join(TEMPLATE_DEST, "src/main.rs"), "w", encoding="utf-8") as f:
        f.write(rust_code)
    return TEMPLATE_DEST


def query_code(prompt: str, model: str) -> Tuple[str, str, int, int] | None:
    response, prompt_tokens, completion_tokens = request(prompt, model, "Rust")
    logging.debug(response)
    logging.debug("--------------------------------")
    if not response:
        return None

    # Extract and combine code blocks
    code_blocks = find_code_blocks_with_language(response)

    # if we have > 1 code blocks and code block > 1 has a fn main
    # then remove any fn main from code block 0
    # otherwise we have two fn main
    if len(code_blocks) >= 2 and code_blocks[1][1].find("fn main") != -1:
        code_blocks[0] = (
            code_blocks[0][0],
            remove_rust_main_function(code_blocks[0][1]),
        )

    rust_code = "\n".join(
        code for lang, code in code_blocks if lang.lower() in ["rust", "rs"]
    )
    logging.debug(rust_code)
    return rust_code, response, prompt_tokens, completion_tokens


def run_cargo_check(code_path: str) -> Result:
    errors = []
    try:
        result = subprocess.run(
            ["cargo", "check", "--message-format=json"],
            cwd=code_path,
            capture_output=True,
            check=False,
        )

        # Parse the JSON output line by line
        for line in result.stdout.decode().split("\n"):
            if line.strip():
                msg = json.loads(line)
                if msg.get("reason") == "compiler-message":
                    if msg.get("message", {}).get("level") == "error":
                        error_msg = msg.get("message", {}).get(
                            "rendered", "Unknown error"
                        )
                        logging.error("Cargo check error: %s", error_msg)
                        errors.append(error_msg)

        return Result(success=result.returncode == 0, errors=errors)

    except (subprocess.SubprocessError, json.JSONDecodeError) as e:
        logging.error("Error during cargo check: %s", e)
        return Result(success=False, errors=[str(e)])


def run_rust_project(code_path: str) -> Tuple[threading.Thread, Popen[Any] | None]:
    """
    Runs the Rust project in a separate thread.

    Args:
        code_path: Path to the Rust project directory

    Returns:
        Tuple containing (thread_handle, process_handle)
    """
    process = None

    def run_target():
        nonlocal process
        try:
            process = Popen(
                ["cargo", "run"],
                cwd=code_path,
            )
        except subprocess.SubprocessError as e:
            logging.error("Error running Rust project: %s", e)

    thread = threading.Thread(target=run_target)
    thread.start()

    # Wait briefly to ensure process is created
    thread.join(0.2)

    return thread, process


def run_rust_project_with_output(code_path: str) -> Result:
    """
    Runs the Rust project and returns its output.
    Times out after 5 seconds.

    Args:
        code_path: Path to the Rust project directory

    Returns:
        Result object containing success status and either output or error message
    """
    try:
        result = subprocess.run(
            ["cargo", "run", "-q"],
            cwd=code_path,
            capture_output=True,
            text=True,
            timeout=60,  # 5 second timeout
            check=False,
        )

        if result.stderr:
            logging.debug("Raw Err Output: %s", result.stderr)
            if (
                result.stderr.find("error:") != -1
                or result.stderr.find("panicked") != -1
                or result.stderr.find("RUST_BACKTRACE") != -1
            ):
                return Result(success=False, errors=[result.stderr])

        logging.debug("Raw Output: %s", result.stdout)
        return Result(success=True, errors=[result.stdout])

    except subprocess.TimeoutExpired:
        logging.error("Rust project execution timed out after 5 seconds")
        return Result(success=False, errors=["Execution timed out after 5 seconds"])
    except subprocess.SubprocessError as e:
        logging.error("Error running Rust project: %s", e)
        return Result(success=False, errors=[str(e)])


def remove_rust_main_function(code: str) -> str:
    """
    Removes any Rust 'fn main' function from the provided code string, even if
    there are braces in raw strings, nested blocks, etc.
    """
    # Regex to find the *start* of fn main:
    #   - Optional attributes (#[...])
    #   - Optional 'async'
    #   - 'fn main' with optional spaces
    #   - '( )' for parameters
    #   - Optional return type with parentheses/brackets
    #   - The '{' that starts the function body
    pattern = re.compile(
        r"(?:\#\[.*?\]\s*)*"  # zero or more attributes like #[tokio::main]
        r"(?:async\s+)?"  # optional 'async'
        r"fn\s+main\s*"  # 'fn main' plus optional whitespace
        r"\(\s*\)\s*"  # the ( ) for main, possibly with spaces
        r"(?:->\s*[\w:<,>\(\)\[\]\s]+)?"  # optional return type e.g. -> Result<...>
        r"\s*\{",  # the opening brace
        re.DOTALL,
    )

    # Find all possible starts of fn main.
    matches = list(pattern.finditer(code))
    if not matches:
        return code  # No fn main found

    # We'll collect the slices of code to keep.
    # We'll remove everything from match.start() to the matching '}'.
    to_keep = []
    last_end = 0

    for match in matches:
        start_index = match.start()
        # Add the code *before* this main function to the kept text.
        to_keep.append(code[last_end:start_index])

        # We'll now find the matching brace after `match.end() - 1`.
        # We already know there's an opening '{' at match.end() - 1.
        brace_count = 1
        pos = match.end()  # Start scanning right *after* the '{'

        while pos < len(code) and brace_count > 0:
            if code[pos] == "{":
                brace_count += 1
            elif code[pos] == "}":
                brace_count -= 1
            pos += 1

        # By now, pos is either:
        # - Just after the matching '}' (brace_count == 0)
        # - Or the end of file if braces never matched up
        last_end = pos  # We'll skip everything from 'start_index' to 'pos'

    # Finally, add any leftover code after the last removed main function
    to_keep.append(code[last_end:])

    return "".join(to_keep)
