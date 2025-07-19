import os
import subprocess
import logging
from typing import List, Optional

from base_executor import BaseLanguageUtils
from utils import Result


class TypeScriptUtils(BaseLanguageUtils):
    """TypeScript-specific language utilities."""
    
    def __init__(self):
        super().__init__(
            language="TypeScript",
            template_name="typescript_container",
            main_file="src/index.ts"
        )
    
    def get_language_aliases(self) -> List[str]:
        """Return TypeScript language aliases."""
        return ["typescript", "ts"]
    
    def run_validation(self, code_path: str) -> Result:
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
    
    def get_run_command(self) -> List[str]:
        """Get command to run TypeScript code."""
        return ["pnpm", "dev"]
    
    def get_build_command(self) -> Optional[List[str]]:
        """Get the build command for TypeScript."""
        return ["pnpm", "run", "build"]
    
    def extract_build_errors(self, stdout: str, stderr: str) -> List[str]:
        """Extract TypeScript-specific build errors."""
        errors = []
        if stderr:
            errors.append(stderr)
        if stdout and "error" in stdout.lower():
            errors.append(stdout)
        return errors if errors else ["Build failed"]
    
    def extract_runtime_errors(self, stdout: str, stderr: str) -> List[str]:
        """Extract TypeScript-specific runtime errors."""
        if stderr and (
            "error" in stderr.lower() or "failed" in stderr.lower()
        ):
            return [stderr]
        return ["Runtime error occurred"]
    
    def run_script(self, code_path: str, timeout: int = 60) -> Result:
        """
        Runs the TypeScript project and returns its output.
        """
        try:
            result = subprocess.run(
                ["pnpm", "dev"],
                cwd=code_path,
                capture_output=True,
                text=True,
                timeout=timeout,
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
            return Result(success=True, errors=[], output=filtered_output)

        except subprocess.TimeoutExpired:
            logging.error(f"TypeScript project execution timed out after {timeout} seconds")
            return Result(success=False, errors=[f"Execution timed out after {timeout} seconds"])
        except subprocess.SubprocessError as e:
            logging.error("Error running TypeScript project: %s", e)
            return Result(success=False, errors=[str(e)])
    
    def prepare_codebase_for_call(self, code: str, input_contents: str) -> str:
        """
        Prepare TypeScript code for TaskCall execution by wrapping it with input handling.
        """
        # For TypeScript, we need to add code to parse input and call the function
        wrapped_code = f"""
{code.strip()}

// Main execution
const input = `{input_contents}`;
const result = example(input);
console.log(result);
"""
        return self.prepare_codebase(wrapped_code)


# Create singleton instance
typescript_utils = TypeScriptUtils()

# Export backward-compatible functions
prepare_codebase = typescript_utils.prepare_codebase
query_code = typescript_utils.query_code
run_tsc_check = typescript_utils.run_validation
run_typescript_project_with_output = typescript_utils.run_script