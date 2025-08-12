import os
import re
import subprocess
import logging
from typing import List, Optional, Tuple

from base_executor import BaseLanguageUtils
from utils import Result


class ZigUtils(BaseLanguageUtils):
    """Zig-specific language utilities."""

    def __init__(self, use_docker: bool = False):
        super().__init__(
            language="Zig",
            template_name="zig_container",
            main_file="src/main.zig",
            use_docker=use_docker,
        )

    def get_language_aliases(self) -> List[str]:
        """Return Zig language aliases."""
        return ["zig", "ziglang"]

    def extract_language_code(self, code_blocks: List[Tuple[str, str]]) -> str:
        """Extract Zig code blocks."""
        # Extract matching code blocks
        aliases = self.get_language_aliases()
        matching_code = []
        for lang, code in code_blocks:
            if lang.lower() in aliases:
                matching_code.append(code)
        
        zig_code = "\n".join(matching_code)
        
        # Add necessary imports if not present
        if "@import" not in zig_code and "pub fn main" in zig_code:
            # Add std import if main function exists but no imports
            imports = """const std = @import("std");

"""
            zig_code = imports + zig_code
        
        return zig_code

    def run_validation(self, code_path: str) -> Result:
        """Run Zig compilation check."""
        errors = []
        try:
            # Try to build the Zig code
            result = subprocess.run(
                ["zig", "build-exe", "src/main.zig", "-femit-bin=main"],
                cwd=code_path,
                capture_output=True,
                text=True,
                check=False,
            )
            
            if result.returncode != 0:
                # Extract error messages from Zig output
                if result.stderr:
                    for line in result.stderr.split("\n"):
                        if "error:" in line:
                            errors.append(line)
                if not errors and result.stderr:
                    errors.append(result.stderr)
                if not errors:
                    errors.append("Compilation failed")
                logging.error("Zig compilation failed: %s", result.stderr)
            
            return Result(success=result.returncode == 0, errors=errors)
        
        except subprocess.SubprocessError as e:
            logging.error("Error during Zig compilation: %s", e)
            return Result(success=False, errors=[str(e)])

    def get_run_command(self) -> List[str]:
        """Get command to run Zig code."""
        return ["./main"]

    def get_build_command(self) -> Optional[List[str]]:
        """Get build command for Zig."""
        return ["zig", "build-exe", "src/main.zig", "-femit-bin=main"]

    def extract_build_errors(self, stdout: str, stderr: str) -> List[str]:
        """Extract Zig-specific build errors."""
        errors = []
        combined = stdout + "\n" + stderr
        for line in combined.split("\n"):
            if "error:" in line or "error note:" in line:
                errors.append(line.strip())
        return errors if errors else ["Build failed"]

    def extract_runtime_errors(self, stdout: str, stderr: str) -> List[str]:
        """Extract Zig-specific runtime errors."""
        if stderr:
            if (
                "panic:" in stderr
                or "unreachable" in stderr
                or "thread" in stderr and "panic" in stderr
                or "segmentation fault" in stderr.lower()
            ):
                return [stderr]
        return ["Runtime error occurred"]

    def run_script(self, code_path: str, timeout: int = 60) -> Result:
        """
        Compiles and runs the Zig code and returns its output.
        """
        try:
            # First, compile the Zig code
            compile_result = subprocess.run(
                ["zig", "build-exe", "src/main.zig", "-femit-bin=main"],
                cwd=code_path,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            
            if compile_result.returncode != 0:
                logging.error("Zig compilation failed: %s", compile_result.stderr)
                errors = self.extract_build_errors(compile_result.stdout, compile_result.stderr)
                return Result(success=False, errors=errors)
            
            # Then, run the executable
            run_result = subprocess.run(
                ["./main"],
                cwd=code_path,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
            
            if run_result.stderr:
                logging.debug("Raw Err Output: %s", run_result.stderr)
                if "panic:" in run_result.stderr or "unreachable" in run_result.stderr:
                    return Result(success=False, errors=[run_result.stderr])
            
            logging.debug("Raw Output: %s", run_result.stdout)
            return Result(success=True, errors=[], output=run_result.stdout)
        
        except subprocess.TimeoutExpired:
            logging.error(f"Zig execution timed out after {timeout} seconds")
            return Result(
                success=False, errors=[f"Execution timed out after {timeout} seconds"]
            )
        except subprocess.SubprocessError as e:
            logging.error("Error running Zig code: %s", e)
            return Result(success=False, errors=[str(e)])

    def prepare_codebase(self, code: str) -> str:
        """
        Override prepare_codebase to ensure Zig code always has a main function.
        """
        # Check if code already has a main function
        if "pub fn main" in code:
            # Code already has main, use parent's prepare_codebase
            return super().prepare_codebase(code)
        
        # Add empty main function for compilation
        wrapped_code = f"""{code.strip()}

pub fn main() void {{
    // Empty main function for compilation
}}
"""
        return super().prepare_codebase(wrapped_code)

    def prepare_codebase_for_call(self, code: str, input_contents: str) -> str:
        """
        Prepare Zig code for TaskCall execution by wrapping it with input handling.
        """
        # Escape the input contents for Zig string literal
        # Zig uses \\ for backslash and \" for quotes
        escaped_input = input_contents.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
        
        # Check if code already has std import
        has_std_import = "@import(\"std\")" in code or '@import("std")' in code
        
        # Only add std import if not already present
        std_import = "" if has_std_import else "const std = @import(\"std\");\n\n"
        
        # Fix for loop syntax for Zig 0.13
        # Old syntax: for (input) |b, i| { ... }
        # New syntax: for (input, 0..) |b, i| { ... }
        def fix_for_loop(match):
            # Extract the iterable part and the capture variables
            full_match = match.group(0)
            iterable = match.group(1)
            value_var = match.group(2)
            index_var = match.group(3)
            return f'for ({iterable}, 0..) |{value_var}, {index_var}|'
        
        fixed_code = re.sub(
            r'for\s*\(([^)]+)\)\s*\|([^,]+),\s*([^|]+)\|',
            fix_for_loop,
            code
        )
        
        wrapped_code = f"""
{std_import}{fixed_code.strip()}

pub fn main() !void {{
    const allocator = std.heap.page_allocator;
    const input = "{escaped_input}";
    const result = try example(allocator, input);
    defer allocator.free(result);
    
    const stdout = std.io.getStdOut().writer();
    try stdout.print("{{s}}\\n", .{{result}});
}}
"""
        return self.prepare_codebase(wrapped_code)


# Create singleton instance
zig_utils = ZigUtils()

# Export backward-compatible functions
prepare_codebase = zig_utils.prepare_codebase
query_code = zig_utils.query_code
run_zig_check = zig_utils.run_validation
run_zig_project_with_output = zig_utils.run_script