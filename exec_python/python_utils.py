import os
import subprocess
import logging
import json
from typing import List

from base_executor import BaseLanguageUtils
from utils import Result


class PythonUtils(BaseLanguageUtils):
    """Python-specific language utilities."""
    
    def __init__(self):
        super().__init__(
            language="Python",
            template_name="python_container",
            main_file="main.py"
        )
    
    def get_language_aliases(self) -> List[str]:
        """Return Python language aliases."""
        return ["python", "py"]
    
    def prepare_codebase_for_call(self, code: str, input_contents: str) -> str:
        """
        Prepare Python code for TaskCall execution by wrapping it with input handling.
        """
        wrapped_code = f"""
{code.strip()}

if __name__ == "__main__":
    import sys
    print(example(r'''{input_contents}'''))
"""
        return self.prepare_codebase(wrapped_code)
    
    def run_validation(self, code_path: str) -> Result:
        """Run pylint on the Python code to check for errors."""
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
    
    def get_run_command(self) -> List[str]:
        """Get command to run Python code."""
        return ["poetry", "run", "python", "main.py"]
    
    def extract_runtime_errors(self, stdout: str, stderr: str) -> List[str]:
        """Extract Python-specific runtime errors."""
        if stderr:
            return [stderr]
        return ["Runtime error occurred"]


# Create singleton instance
python_utils = PythonUtils()

# Export backward-compatible functions
prepare_codebase = python_utils.prepare_codebase
query_code = python_utils.query_code
run_pylint_check = python_utils.run_validation
run_python_script = python_utils.run_script