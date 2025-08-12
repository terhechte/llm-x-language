import os
import re
import subprocess
import logging
from typing import List, Optional, Tuple

from base_executor import BaseLanguageUtils
from utils import Result
from docker_utils import docker_start_attach, docker_stop_rm


class JavaUtils(BaseLanguageUtils):
    """Java-specific language utilities."""

    def __init__(self, use_docker: bool = False):
        super().__init__(
            language="Java",
            template_name="java_container",
            main_file="src/main/java/Main.java",
            use_docker=use_docker,
        )

    def get_language_aliases(self) -> List[str]:
        """Return Java language aliases."""
        return ["java", "jav"]

    def extract_language_code(self, code_blocks: List[Tuple[str, str]]) -> str:
        """Extract Java code blocks."""
        # Extract matching code blocks
        aliases = self.get_language_aliases()
        matching_code = []
        for lang, code in code_blocks:
            if lang.lower() in aliases:
                matching_code.append(code)
        
        java_code = "\n".join(matching_code)
        
        # Add necessary imports if not present
        if "import" not in java_code and "class" in java_code:
            # Add common imports if they seem to be missing
            imports = """import java.util.*;
import java.io.*;
import com.fasterxml.jackson.databind.*;
import okhttp3.*;
import static spark.Spark.*;

"""
            java_code = imports + java_code
        
        # Ensure we have a Main class if not present
        if "class Main" not in java_code and "public static void main" in java_code:
            # Wrap loose main method in Main class
            if "public static void main" in java_code:
                # Find where main method starts
                main_start = java_code.find("public static void main")
                before_main = java_code[:main_start].rstrip()
                main_and_after = java_code[main_start:]
                
                java_code = f"""{before_main}

public class Main {{
    {main_and_after}
}}"""
        
        return java_code

    def run_validation(self, code_path: str) -> Result:
        """Run Java compilation check."""
        errors = []
        try:
            # Run Maven compile
            result = subprocess.run(
                ["mvn", "compile", "-q"],
                cwd=code_path,
                capture_output=True,
                text=True,
                check=False,
            )
            
            if result.returncode != 0:
                # Extract error messages from Maven output
                if result.stdout:
                    for line in result.stdout.split("\n"):
                        if "ERROR]" in line:
                            errors.append(line)
                if result.stderr:
                    for line in result.stderr.split("\n"):
                        if "error:" in line.lower():
                            errors.append(line)
                if not errors:
                    errors.append("Compilation failed")
                logging.error("Maven compilation failed: %s", result.stderr or result.stdout)
            
            return Result(success=result.returncode == 0, errors=errors)
        
        except subprocess.SubprocessError as e:
            logging.error("Error during Java compilation: %s", e)
            return Result(success=False, errors=[str(e)])


    def get_run_command(self) -> List[str]:
        """Get command to run Java code - compile and run in one step for Docker."""
        # For Docker, combine compile and run to ensure proper execution
        if self._use_docker():
            return ["sh", "-c", "mvn compile -q && java -cp target/classes:target/dependency/* Main"]
        else:
            # For native execution, just run (assumes already compiled)
            return ["java", "-cp", "target/classes:target/dependency/*", "Main"]
    
    def get_validation_command(self) -> Optional[List[str]]:
        """Get command to validate Java code."""
        return ["javac", "-Xlint:all", "Main.java"]

    def get_build_command(self) -> Optional[List[str]]:
        """Get build command for Java."""
        # Skip separate build for Docker since compile is done in get_run_command
        if self._use_docker():
            return None
        return ["mvn", "compile", "-q"]

    def extract_build_errors(self, stdout: str, stderr: str) -> List[str]:
        """Extract Java-specific build errors."""
        errors = []
        combined = stdout + "\n" + stderr
        for line in combined.split("\n"):
            if "error:" in line.lower() or "[ERROR]" in line:
                errors.append(line.strip())
        return errors if errors else ["Build failed"]

    def extract_runtime_errors(self, stdout: str, stderr: str) -> List[str]:
        """Extract Java-specific runtime errors."""
        if stderr:
            if (
                "Exception" in stderr
                or "Error" in stderr
                or "at java." in stderr
                or "at com." in stderr
            ):
                return [stderr]
        return ["Runtime error occurred"]

    def run_script(self, code_path: str, timeout: int = 60) -> Result:
        """
        Compiles and runs the Java code and returns its output.
        """
        try:
            # First, compile with Maven
            compile_result = subprocess.run(
                ["mvn", "compile", "-q"],
                cwd=code_path,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            
            if compile_result.returncode != 0:
                logging.error("Maven compilation failed: %s", compile_result.stderr or compile_result.stdout)
                errors = self.extract_build_errors(compile_result.stdout, compile_result.stderr)
                return Result(success=False, errors=errors)
            
            # Then, run the Java application
            run_result = subprocess.run(
                ["java", "-cp", "target/classes:target/dependency/*", "Main"],
                cwd=code_path,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
            
            if run_result.stderr:
                logging.debug("Raw Err Output: %s", run_result.stderr)
                if "Exception" in run_result.stderr or "Error" in run_result.stderr:
                    return Result(success=False, errors=[run_result.stderr])
            
            logging.debug("Raw Output: %s", run_result.stdout)
            return Result(success=True, errors=[], output=run_result.stdout)
        
        except subprocess.TimeoutExpired:
            logging.error(f"Java execution timed out after {timeout} seconds")
            return Result(
                success=False, errors=[f"Execution timed out after {timeout} seconds"]
            )
        except subprocess.SubprocessError as e:
            logging.error("Error running Java code: %s", e)
            return Result(success=False, errors=[str(e)])

    def prepare_codebase(self, code: str) -> str:
        """
        Override prepare_codebase to ensure Java code always has a Main class.
        """
        # Check if code already has a Main class
        if "class Main" in code or "public class Main" in code:
            # Code already has Main class, use parent's prepare_codebase
            return super().prepare_codebase(code)
        
        # Check if code has a main method but no Main class
        if "public static void main" in code:
            # Already handled in extract_language_code
            return super().prepare_codebase(code)
        
        # Add empty Main class with main method for type checking
        wrapped_code = f"""{code.strip()}

public class Main {{
    public static void main(String[] args) {{
        // Empty main method for compilation
    }}
}}
"""
        return super().prepare_codebase(wrapped_code)

    def prepare_codebase_for_call(self, code: str, input_contents: str) -> str:
        """
        Prepare Java code for TaskCall execution by wrapping it with input handling.
        """
        # Escape the input contents for Java string literal
        escaped_input = input_contents.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
        
        # Parse the code to find the class name and method
        clean_code = code.strip()
        
        # Check if the LLM generated a class with the example method
        class_match = re.search(r'public\s+class\s+(\w+)', clean_code)
        has_utils_class = class_match and class_match.group(1) != 'Main'
        
        if has_utils_class:
            # The LLM generated a separate class (like Utils)
            # We need to call ClassName.example() instead of just example()
            class_name = class_match.group(1)
            
            # Only keep the class definition that contains the example method
            # Remove any duplicate Main class if present
            if "public class Main" in clean_code:
                # Extract just the non-Main class
                parts = clean_code.split("public class Main")
                clean_code = parts[0].strip()
            
            # Make the Utils class non-public since it's in Main.java file
            # Java only allows one public class per file and it must match the filename
            clean_code_non_public = clean_code.replace(f"public class {class_name}", f"class {class_name}")
            
            wrapped_code = f"""
{clean_code_non_public}

public class Main {{
    public static void main(String[] args) {{
        String input = "{escaped_input}";
        String result = {class_name}.example(input);
        System.out.println(result);
    }}
}}
"""
        else:
            # The LLM didn't generate a separate class or generated Main class
            # Check if there's already an example method in Main
            if "public class Main" in clean_code and "example" in clean_code:
                # The code already has Main class with example method
                # Just ensure proper structure
                wrapped_code = clean_code
            else:
                # No class structure, just the method - put it inside Main
                wrapped_code = f"""
public class Main {{
    {clean_code.strip()}
    
    public static void main(String[] args) {{
        String input = "{escaped_input}";
        String result = example(input);
        System.out.println(result);
    }}
}}
"""
        return self.prepare_codebase(wrapped_code)


# Create singleton instance
java_utils = JavaUtils()

# Export backward-compatible functions
prepare_codebase = java_utils.prepare_codebase
query_code = java_utils.query_code
run_java_check = java_utils.run_validation
run_java_project_with_output = java_utils.run_script