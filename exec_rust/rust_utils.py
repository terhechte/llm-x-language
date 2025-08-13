import os
import re
import subprocess
import logging
import json
from typing import List, Tuple, Optional

from base_executor import BaseLanguageUtils
from utils import Result


class RustUtils(BaseLanguageUtils):
    """Rust-specific language utilities."""

    def __init__(self, use_docker: bool = False):
        super().__init__(
            language="Rust",
            template_name="rust_container",
            main_file="src/main.rs",
            use_docker=use_docker,
        )

    def get_language_aliases(self) -> List[str]:
        """Return Rust language aliases."""
        return ["rust", "rs"]

    def extract_language_code(self, code_blocks: List[Tuple[str, str]]) -> str:
        """
        Extract Rust code blocks with special handling for duplicate main functions.
        """
        # If we have > 1 code blocks and code block > 1 has a fn main
        # then remove any fn main from code block 0
        # otherwise we have two fn main
        if len(code_blocks) >= 2 and code_blocks[1][1].find("fn main") != -1:
            code_blocks[0] = (
                code_blocks[0][0],
                self.remove_rust_main_function(code_blocks[0][1]),
            )

        # Extract matching code blocks
        aliases = self.get_language_aliases()
        matching_code = []
        for lang, code in code_blocks:
            if lang.lower() in aliases:
                matching_code.append(code)

        return "\n".join(matching_code)

    def run_validation(self, code_path: str) -> Result:
        """Run cargo check for code validation."""
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

    def get_run_command(self) -> List[str]:
        """Get command to run Rust code."""
        return ["cargo", "run"]
    
    def get_validation_command(self) -> Optional[List[str]]:
        """Get command to validate Rust code."""
        return ["cargo", "check"]

    def get_build_command(self) -> Optional[List[str]]:
        """Get the build command for Rust.

        Skip explicit pre-build; `cargo run -q` compiles as needed. This
        avoids redundant builds and reduces timeouts under parallel load.
        """
        return None

    def extract_build_errors(self, stdout: str, stderr: str) -> List[str]:
        """Extract Rust-specific build errors."""
        errors = []
        if stderr and ("error:" in stderr or "error[" in stderr):
            errors.append(stderr)
        return errors if errors else ["Build failed"]

    def extract_runtime_errors(self, stdout: str, stderr: str) -> List[str]:
        """Extract Rust-specific runtime errors."""
        if stderr:
            if (
                stderr.find("error:") != -1
                or stderr.find("panicked") != -1
                or stderr.find("RUST_BACKTRACE") != -1
            ):
                return [stderr]
        return ["Runtime error occurred"]

    def run_script(self, code_path: str, timeout: int = 60) -> Result:
        """
        Runs the Rust project and returns its output.
        """
        try:
            result = subprocess.run(
                ["cargo", "run", "-q"],
                cwd=code_path,
                capture_output=True,
                text=True,
                timeout=timeout,
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
            return Result(success=True, errors=[], output=result.stdout)

        except subprocess.TimeoutExpired:
            logging.error(f"Rust project execution timed out after {timeout} seconds")
            return Result(
                success=False, errors=[f"Execution timed out after {timeout} seconds"]
            )
        except subprocess.SubprocessError as e:
            logging.error("Error running Rust project: %s", e)
            return Result(success=False, errors=[str(e)])

    def prepare_codebase(self, code: str) -> str:
        """
        Override prepare_codebase to ensure Rust code always has a main function.
        This is needed because Rust requires a main function to compile.
        """
        import re
        
        # Use regex to detect main function more accurately
        # This pattern matches fn main with optional pub, return type, and flexible formatting
        main_function_pattern = r'^\s*(pub\s+)?fn\s+main\s*\([^)]*\)\s*(->\s*[^{]+)?\s*\{'
        if re.search(main_function_pattern, code, re.MULTILINE):
            # Code already has main function, use parent's prepare_codebase
            logging.debug("Rust: main function detected, using code as-is")
            return super().prepare_codebase(code)
        
        # Add empty main function for type checking
        wrapped_code = f"""{code.strip()}

fn main() {{
    // Empty main function for type checking
}}
"""
        return super().prepare_codebase(wrapped_code)

    def prepare_codebase_for_call(self, code: str, input_contents: str) -> str:
        """
        Prepare Rust code for TaskCall execution by wrapping it with input handling.
        """
        # For Rust, use raw string literals with enough # to avoid conflicts
        # Count the max consecutive # in the input and use more
        max_hashes = 0
        if '"#' in input_contents:
            import re

            matches = re.findall(r"#+", input_contents)
            if matches:
                max_hashes = max(len(m) for m in matches)

        # Use one more # than found in the input
        hash_count = max_hashes + 1
        hashes = "#" * hash_count

        wrapped_code = f"""
{code.strip()}

fn main() {{
    let input = r{hashes}"{input_contents}"{hashes};
    let result = example(input.to_string());
    println!("{{}}", result);
}}
"""
        return self.prepare_codebase(wrapped_code)

    def remove_rust_main_function(self, code: str) -> str:
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


# Create singleton instance
rust_utils = RustUtils()

# Export backward-compatible functions
prepare_codebase = rust_utils.prepare_codebase
query_code = rust_utils.query_code
run_cargo_check = rust_utils.run_validation
run_rust_project_with_output = rust_utils.run_script
remove_rust_main_function = rust_utils.remove_rust_main_function
