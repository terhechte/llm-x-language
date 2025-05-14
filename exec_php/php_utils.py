import os
import subprocess
import logging
import json
from dataclasses import dataclass
from typing import List, Optional
from typing import Tuple, Optional
from llm import request
from utils import find_code_blocks_with_language, Result


TEMPLATE = "php_container"
TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "../../", TEMPLATE)
TEMPLATE_DEST = os.path.join(os.path.dirname(__file__), "../dojo", TEMPLATE)

def query_code(prompt: str, model: str) -> Optional[Tuple[str, str, int, int]]:
    """
    Process the code for PHP execution
    """
    response, prompt_tokens, completion_tokens = request(prompt, model, "PHP")
    logging.debug(response)
    logging.debug("--------------------------------")
    if not response:
        return None

    code_blocks = find_code_blocks_with_language(response)
    php_code = "\n".join(
        code for lang, code in code_blocks if lang.lower() in ["php"]
    )
    logging.debug(php_code)
    return php_code, response, prompt_tokens, completion_tokens


def prepare_codebase(php_code: str) -> str:
    """
    Prepares the PHP codebase by creating necessary files
    """
     # Write the Python code to main.py
    with open(os.path.join(TEMPLATE_DEST, "main.php"), "w", encoding="utf-8") as f:
        f.write(php_code)
    return TEMPLATE_DEST


def run_php_check(code_path: str) -> Result:
    """
    Runs PHP syntax check on the code
    Returns a Result object with success status and any errors found
    """
    try:
        result = subprocess.run(
            ["php", "-l", os.path.join(code_path, "main.php")],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            return Result(success=True, errors=[])
        
        errors = []
        if result.stderr:
            errors = [line for line in result.stderr.split('\n') if line.strip()]
        
        return Result(success=False, errors=errors)
    except subprocess.SubprocessError as e:
        logging.error("Error during PHP syntax check: %s", e)
        return Result(success=False, errors=[str(e)])


def run_php_script(code_path: str) -> Result:
    """
    Runs the PHP script and returns the output
    """
    try:
        result = subprocess.run(
            ["php", os.path.join(code_path, "main.php")],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode != 0:
            return Result(success=False, errors=[result.stderr])
        
        return Result(success=True, errors=[result.stdout])
    except subprocess.SubprocessError as e:
        logging.error("Error running PHP script: %s", e)
        return Result(success=False, errors=[str(e)])