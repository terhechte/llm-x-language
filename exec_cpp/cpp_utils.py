import os
import re
import subprocess
import logging
from typing import List, Optional, Tuple

from base_executor import BaseLanguageUtils
from utils import Result


class CppUtils(BaseLanguageUtils):
    """C++-specific language utilities."""

    def __init__(self, use_docker: bool = False):
        super().__init__(
            language="C++",
            template_name="cpp_container",
            main_file="src/main.cpp",
            use_docker=use_docker,
        )
        # Override docker_image since "c++" is not a valid Docker image name
        self.docker_image = "llm-benchmark/cpp"

    def get_language_aliases(self) -> List[str]:
        """Return C++ language aliases."""
        return ["cpp", "c++", "cplusplus", "cxx"]

    def extract_language_code(self, code_blocks: List[Tuple[str, str]]) -> str:
        """Extract C++ code blocks."""
        # Extract matching code blocks
        aliases = self.get_language_aliases()
        matching_code = []
        for lang, code in code_blocks:
            if lang.lower() in aliases:
                matching_code.append(code)
        
        cpp_code = "\n".join(matching_code)
        
        # Add necessary includes if not present
        if "#include" not in cpp_code:
            includes = """#include <iostream>
#include <string>
#include <vector>
#include <sstream>
#include <curl/curl.h>
#include <nlohmann/json.hpp>

using json = nlohmann::json;
using namespace std;

"""
            cpp_code = includes + cpp_code
        
        return cpp_code

    def run_validation(self, code_path: str) -> Result:
        """Run C++ compilation check."""
        errors = []
        try:
            # Run cmake to configure
            cmake_result = subprocess.run(
                ["cmake", "."],
                cwd=code_path,
                capture_output=True,
                text=True,
                check=False,
            )
            
            if cmake_result.returncode != 0:
                logging.error("CMake configuration failed: %s", cmake_result.stderr)
                errors.append(cmake_result.stderr)
                return Result(success=False, errors=errors)
            
            # Run make to compile
            make_result = subprocess.run(
                ["make"],
                cwd=code_path,
                capture_output=True,
                text=True,
                check=False,
            )
            
            if make_result.returncode != 0:
                # Extract error messages from make output
                if make_result.stderr:
                    for line in make_result.stderr.split("\n"):
                        if "error:" in line.lower():
                            errors.append(line)
                if not errors:
                    errors.append("Compilation failed")
                logging.error("Make compilation failed: %s", make_result.stderr)
            
            return Result(success=make_result.returncode == 0, errors=errors)
        
        except subprocess.SubprocessError as e:
            logging.error("Error during C++ compilation: %s", e)
            return Result(success=False, errors=[str(e)])

    def get_run_command(self) -> List[str]:
        """Get command to run C++ code."""
        return ["./main"]

    def get_build_command(self) -> Optional[List[str]]:
        """Get build command for C++."""
        # We'll build as part of run_script
        return None

    def extract_build_errors(self, stdout: str, stderr: str) -> List[str]:
        """Extract C++-specific build errors."""
        errors = []
        if stderr:
            for line in stderr.split("\n"):
                if "error:" in line.lower() or "undefined reference" in line:
                    errors.append(line)
        return errors if errors else ["Build failed"]

    def extract_runtime_errors(self, stdout: str, stderr: str) -> List[str]:
        """Extract C++-specific runtime errors."""
        if stderr:
            if (
                "segmentation fault" in stderr.lower()
                or "core dumped" in stderr.lower()
                or "abort" in stderr.lower()
                or "terminate" in stderr.lower()
                or "exception" in stderr.lower()
            ):
                return [stderr]
        return ["Runtime error occurred"]

    def run_script(self, code_path: str, timeout: int = 60) -> Result:
        """
        Compiles and runs the C++ code and returns its output.
        """
        try:
            # First, run cmake
            cmake_result = subprocess.run(
                ["cmake", "."],
                cwd=code_path,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            
            if cmake_result.returncode != 0:
                logging.error("CMake failed: %s", cmake_result.stderr)
                return Result(success=False, errors=[cmake_result.stderr])
            
            # Then, compile with make
            make_result = subprocess.run(
                ["make"],
                cwd=code_path,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            
            if make_result.returncode != 0:
                logging.error("Make failed: %s", make_result.stderr)
                return Result(success=False, errors=[make_result.stderr])
            
            # Finally, run the executable
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
                if (
                    "segmentation fault" in run_result.stderr.lower()
                    or "core dumped" in run_result.stderr.lower()
                    or "abort" in run_result.stderr.lower()
                ):
                    return Result(success=False, errors=[run_result.stderr])
            
            logging.debug("Raw Output: %s", run_result.stdout)
            return Result(success=True, errors=[], output=run_result.stdout)
        
        except subprocess.TimeoutExpired:
            logging.error(f"C++ execution timed out after {timeout} seconds")
            return Result(
                success=False, errors=[f"Execution timed out after {timeout} seconds"]
            )
        except subprocess.SubprocessError as e:
            logging.error("Error running C++ code: %s", e)
            return Result(success=False, errors=[str(e)])

    def prepare_codebase(self, code: str) -> str:
        """
        Override prepare_codebase to ensure C++ code always has a main function.
        """
        # Check if code already has a main function
        if "int main" in code or "main(" in code:
            # Code already has main, use parent's prepare_codebase
            return super().prepare_codebase(code)
        
        # Add empty main function for type checking
        wrapped_code = f"""{code.strip()}

int main() {{
    // Empty main function for compilation
    return 0;
}}
"""
        return super().prepare_codebase(wrapped_code)

    def prepare_codebase_for_call(self, code: str, input_contents: str) -> str:
        """
        Prepare C++ code for TaskCall execution by wrapping it with input handling.
        """
        # Escape the input contents for C++ string literal
        escaped_input = input_contents.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
        
        # Ensure necessary includes are present
        clean_code = code.strip()
        
        # Check which includes are missing and add them
        includes_to_add = []
        if "#include <iostream>" not in clean_code:
            includes_to_add.append("#include <iostream>")
        if "#include <string>" not in clean_code and "std::string" in clean_code:
            includes_to_add.append("#include <string>")
        
        # Add includes at the beginning if needed
        if includes_to_add:
            includes = "\n".join(includes_to_add) + "\n\n"
            clean_code = includes + clean_code
        
        wrapped_code = f"""
{clean_code}

int main() {{
    std::string input = "{escaped_input}";
    std::string result = example(input);
    std::cout << result << std::endl;
    return 0;
}}
"""
        return self.prepare_codebase(wrapped_code)


# Create singleton instance
cpp_utils = CppUtils()

# Export backward-compatible functions
prepare_codebase = cpp_utils.prepare_codebase
query_code = cpp_utils.query_code
run_cpp_check = cpp_utils.run_validation
run_cpp_project_with_output = cpp_utils.run_script