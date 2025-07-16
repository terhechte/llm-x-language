import os
import tempfile
import subprocess
from typing import Optional, Tuple
from utils import Result
from llm import request


def query_code(prompt: str, model: str) -> Optional[Tuple[str, str, int, int]]:
    """
    Query the model for Lua code based on the prompt.
    Returns a tuple of (lua_code, full_response, prompt_tokens, completion_tokens).
    """
    try:
        response, prompt_tokens, completion_tokens = request(prompt, model, "Lua")
        if not response:
            return None
        return response, response, prompt_tokens, completion_tokens
    except Exception as e:
        raise ValueError(f"Failed to query code: {str(e)}")


def prepare_codebase(lua_code: str) -> Optional[str]:
    """
    Prepare a temporary directory with the Lua code.
    Returns the path to the temporary directory.
    """
    try:
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()
        code_path = os.path.join(temp_dir, "main.lua")

        # Write the code to a file
        with open(code_path, "w") as f:
            f.write(lua_code)

        return code_path
    except Exception as e:
        print(f"Error preparing codebase: {e}")
        return None


def run_lua_check(code_path: str) -> Result:
    """
    Run luac -p to check Lua code for syntax errors.
    Returns a Result indicating success/failure and any errors.
    """
    try:
        result = subprocess.run(
            ["luac", "-p", code_path], capture_output=True, text=True, check=False
        )

        if result.returncode != 0:
            return Result(success=False, errors=[result.stderr.strip()])
        return Result(success=True, errors=[])
    except subprocess.CalledProcessError as e:
        return Result(success=False, errors=[str(e)])
    except Exception as e:
        return Result(success=False, errors=[f"Error running lua check: {str(e)}"])


def run_lua_script(code_path: str) -> Result:
    """
    Run a Lua script and capture its output.
    Returns a Result containing success/failure status and output or errors.
    """
    try:
        result = subprocess.run(
            ["lua", code_path], capture_output=True, text=True, check=False
        )

        if result.returncode != 0:
            return Result(success=False, errors=[result.stderr.strip()])
        return Result(success=True, errors=[], output=result.stdout.strip())
    except subprocess.CalledProcessError as e:
        return Result(success=False, errors=[str(e)])
    except Exception as e:
        return Result(success=False, errors=[f"Error running lua script: {str(e)}"])
