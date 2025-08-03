import os
import subprocess
import logging
from typing import List, Optional, Tuple

from base_executor import BaseLanguageUtils
from utils import Result, find_code_blocks_with_language
from llm import request as llm_request


class SwiftUtils(BaseLanguageUtils):
    """Swift-specific language utilities."""

    def __init__(self, use_docker: bool = False):
        super().__init__(
            language="Swift",
            template_name="swift_container",
            main_file="Sources/main.swift",
            use_docker=use_docker,
        )

    def get_language_aliases(self) -> List[str]:
        """Return Swift language aliases."""
        return ["swift"]

    def extract_language_code(self, code_blocks: List[Tuple[str, str]]) -> str:
        """
        Extract Swift code blocks with special handling.
        """
        # Extract matching code blocks
        aliases = self.get_language_aliases()
        matching_code = []
        for lang, code in code_blocks:
            if lang.lower() in aliases:
                matching_code.append(code)

        swift_code = "\n".join(matching_code)

        # Add Foundation import if missing
        if swift_code and swift_code.find("import Foundation") == -1:
            swift_code = "import Foundation\n\n" + swift_code

        # Remove @main annotation if present
        if swift_code.find("@main\n") > -1:
            swift_code = swift_code.replace("@main\n", "\n")

        return swift_code

    def run_validation(self, code_path: str) -> Result:
        """Run swift build to check for compilation errors."""
        errors = []
        try:
            # Clean before build to ensure no stale artifacts
            subprocess.run(
                ["swift", "package", "clean"],
                cwd=code_path,
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
            )

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

    def get_run_command(self) -> List[str]:
        """Get command to run Swift code."""
        return ["swift", "run", "--skip-build"]

    def get_build_command(self) -> Optional[List[str]]:
        """Get the build command for Swift."""
        return ["swift", "build"]

    def extract_build_errors(self, stdout: str, stderr: str) -> List[str]:
        """Extract Swift-specific build errors."""
        errors = []
        if stdout and "error:" in stdout:
            errors.append(stdout)
        if stderr and "error:" in stderr:
            errors.append(stderr)
        return errors if errors else ["Build failed"]

    def extract_runtime_errors(self, stdout: str, stderr: str) -> List[str]:
        """Extract Swift-specific runtime errors."""
        if stderr and "error:" in stderr:
            return [stderr]
        return ["Runtime error occurred"]

    def prepare_codebase_for_call(self, code: str, input_contents: str) -> str:
        """
        Prepare Swift code for TaskCall execution by wrapping it with input handling.
        """
        # Escape the input for Swift multi-line string literal
        # Swift supports """ for multi-line strings which handles quotes naturally
        wrapped_code = f'''
{code.strip()}

// Main execution
let input = """
{input_contents}
"""
let result = example(input: input)
print(result)
'''
        return self.prepare_codebase(wrapped_code)

    def query_code_for_call(
        self, prompt: str, model: str
    ) -> Optional[Tuple[str, str, int, int]]:
        """
        Special query method for TaskCall that filters for functions containing 'func example'.
        """
        response, prompt_tokens, completion_tokens = llm_request(
            prompt, model, self.language
        )
        logging.debug(response)
        if not response:
            return None

        code_blocks = find_code_blocks_with_language(response)
        # Filter for blocks containing 'func example'
        code_blocks = [b for b in code_blocks if b[1].find("func example") != -1]

        swift_code = self.extract_language_code(code_blocks)
        logging.debug(swift_code)
        return swift_code, response, prompt_tokens, completion_tokens


# Create singleton instance
swift_utils = SwiftUtils()

# Export backward-compatible functions
prepare_codebase = swift_utils.prepare_codebase
query_code = swift_utils.query_code
run_swift_check = swift_utils.run_validation
run_swift_project_with_output = swift_utils.run_script
