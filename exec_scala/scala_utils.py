import os
import re
import subprocess
import logging
from typing import List, Optional, Tuple

from base_executor import BaseLanguageUtils
from utils import Result


class ScalaUtils(BaseLanguageUtils):
    """Scala-specific language utilities."""

    def __init__(self, use_docker: bool = False):
        super().__init__(
            language="Scala",
            template_name="scala_container",
            main_file="src/main/scala/Main.scala",
            use_docker=use_docker,
        )

    def get_language_aliases(self) -> List[str]:
        """Return Scala language aliases."""
        return ["scala", "sc"]

    def extract_language_code(self, code_blocks: List[Tuple[str, str]]) -> str:
        """Extract Scala code blocks."""
        # Extract matching code blocks
        aliases = self.get_language_aliases()
        matching_code = []
        for lang, code in code_blocks:
            if lang.lower() in aliases:
                matching_code.append(code)
        
        scala_code = "\n".join(matching_code)
        
        # Add necessary imports if not present
        if "import" not in scala_code and ("println" in scala_code or "Array[String]" in scala_code):
            # Add common imports if they seem to be missing
            imports = """import scala.io.Source
import scala.util.{Try, Success, Failure}
import scala.concurrent.{Future, Promise}
import scala.concurrent.ExecutionContext.Implicits.global

"""
            scala_code = imports + scala_code
        
        # Ensure we have a Main object if not present
        if "object Main" not in scala_code and "def main(" in scala_code:
            # Wrap loose main method in Main object
            if "def main(args: Array[String])" in scala_code:
                # Find where main method starts
                main_start = scala_code.find("def main(args: Array[String])")
                before_main = scala_code[:main_start].rstrip()
                main_and_after = scala_code[main_start:]
                
                scala_code = f"""{before_main}

object Main {{
  {main_and_after}
}}"""
        
        return scala_code

    def run_validation(self, code_path: str) -> Result:
        """Run Scala compilation check."""
        errors = []
        try:
            # Run SBT compile
            result = subprocess.run(
                ["sbt", "-batch", "-error", "compile"],
                cwd=code_path,
                capture_output=True,
                text=True,
                check=False,
                env={**os.environ, "SBT_OPTS": "-Xmx2G"},
            )
            
            if result.returncode != 0:
                # Extract error messages from SBT output
                if result.stdout:
                    for line in result.stdout.split("\n"):
                        if "[error]" in line:
                            errors.append(line)
                if result.stderr:
                    for line in result.stderr.split("\n"):
                        if "error:" in line.lower():
                            errors.append(line)
                if not errors:
                    errors.append("Compilation failed")
                logging.error("SBT compilation failed: %s", result.stderr or result.stdout)
            
            return Result(success=result.returncode == 0, errors=errors)
        
        except subprocess.SubprocessError as e:
            logging.error("Error during Scala compilation: %s", e)
            return Result(success=False, errors=[str(e)])

    def get_run_command(self) -> List[str]:
        """Get command to run Scala code."""
        # Note: Don't use -error flag for run as it suppresses program output
        # In Docker mode, we need to filter SBT output to get only program output
        if self._use_docker():
            # Filter out all SBT metadata lines and extract actual program output
            # Lines starting with [info] that are NOT SBT metadata get the prefix removed
            filter_script = r"""
sbt -batch run | while IFS= read -r line; do
    if [[ "$line" =~ ^\[info\]\ (welcome|loading|compiling|done\ compiling|running|set\ current|Total\ time) ]]; then
        continue
    elif [[ "$line" =~ ^\[success\] ]]; then
        continue
    elif [[ "$line" =~ ^\[info\]\ (.*)$ ]]; then
        echo "${BASH_REMATCH[1]}"
    elif [[ ! "$line" =~ ^\[.*\] ]]; then
        echo "$line"
    fi
done
"""
            return ["bash", "-c", filter_script.strip()]
        else:
            return ["sbt", "-batch", "run"]
    
    def get_validation_command(self) -> Optional[List[str]]:
        """Get command to validate Scala code."""
        return ["sbt", "-batch", "-error", "compile"]

    def get_build_command(self) -> Optional[List[str]]:
        """Get build command for Scala."""
        return ["sbt", "-batch", "-error", "compile"]

    def extract_build_errors(self, stdout: str, stderr: str) -> List[str]:
        """Extract Scala-specific build errors."""
        errors = []
        combined = stdout + "\n" + stderr
        for line in combined.split("\n"):
            if "[error]" in line or "error:" in line.lower():
                # Clean up SBT error formatting
                error_msg = line.replace("[error]", "").strip()
                if error_msg:
                    errors.append(error_msg)
        return errors if errors else ["Build failed"]

    def extract_runtime_errors(self, stdout: str, stderr: str) -> List[str]:
        """Extract Scala-specific runtime errors."""
        if stderr:
            if (
                "Exception" in stderr
                or "Error" in stderr
                or "at scala." in stderr
                or "at java." in stderr
                or "NoSuchMethodError" in stderr
            ):
                return [stderr]
        # Also check stdout for SBT errors
        if "[error]" in stdout:
            errors = []
            for line in stdout.split("\n"):
                if "[error]" in line:
                    errors.append(line)
            if errors:
                return errors
        return ["Runtime error occurred"]

    def run_script(self, code_path: str, timeout: int = 60) -> Result:
        """
        Compiles and runs the Scala code and returns its output.
        """
        try:
            # First, compile with SBT
            compile_result = subprocess.run(
                ["sbt", "-batch", "-error", "compile"],
                cwd=code_path,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
                env={**os.environ, "SBT_OPTS": "-Xmx2G"},
            )
            
            if compile_result.returncode != 0:
                logging.error("SBT compilation failed: %s", compile_result.stderr or compile_result.stdout)
                errors = self.extract_build_errors(compile_result.stdout, compile_result.stderr)
                return Result(success=False, errors=errors)
            
            # Then, run the Scala application
            # Note: Don't use -error flag for run as it suppresses program output
            run_result = subprocess.run(
                ["sbt", "-batch", "run"],
                cwd=code_path,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
                env={**os.environ, "SBT_OPTS": "-Xmx2G"},
            )
            
            # Extract actual output from SBT output
            # When SBT runs in fork mode, it prefixes program output with "[info] "
            output_lines = []
            for line in run_result.stdout.split("\n"):
                # Check if this is program output prefixed with [info]
                if line.startswith("[info] ") and not any(x in line for x in [
                    "welcome to sbt", "loading", "compiling", "running (fork)", 
                    "done compiling", "Total time", "set current project"
                ]):
                    # Extract the actual output after "[info] "
                    output_lines.append(line[7:])  # Remove "[info] " prefix
                elif not line.startswith("[") and line.strip():
                    # Non-prefixed output (shouldn't happen in fork mode but just in case)
                    output_lines.append(line)
            
            clean_output = "\n".join(output_lines)
            
            if run_result.stderr:
                logging.debug("Raw Err Output: %s", run_result.stderr)
                if "Exception" in run_result.stderr or "Error" in run_result.stderr:
                    return Result(success=False, errors=[run_result.stderr])
            
            # Check for errors in stdout (SBT reports some errors there)
            if "[error]" in run_result.stdout:
                errors = self.extract_runtime_errors(run_result.stdout, run_result.stderr)
                return Result(success=False, errors=errors)
            
            logging.debug("Raw Output: %s", clean_output)
            return Result(success=True, errors=[], output=clean_output)
        
        except subprocess.TimeoutExpired:
            logging.error(f"Scala execution timed out after {timeout} seconds")
            return Result(
                success=False, errors=[f"Execution timed out after {timeout} seconds"]
            )
        except subprocess.SubprocessError as e:
            logging.error("Error running Scala code: %s", e)
            return Result(success=False, errors=[str(e)])

    def prepare_codebase(self, code: str) -> str:
        """
        Override prepare_codebase to ensure Scala code always has a Main object.
        """
        # Check if code already has a Main object
        if "object Main" in code:
            # Code already has Main object, use parent's prepare_codebase
            return super().prepare_codebase(code)
        
        # Check if code has a main method but no Main object
        if "def main(args: Array[String])" in code:
            # Already handled in extract_language_code
            return super().prepare_codebase(code)
        
        # Add empty Main object with main method for compilation
        wrapped_code = f"""{code.strip()}

object Main {{
  def main(args: Array[String]): Unit = {{
    // Empty main method for compilation
  }}
}}
"""
        return super().prepare_codebase(wrapped_code)

    def prepare_codebase_for_call(self, code: str, input_contents: str) -> str:
        """
        Prepare Scala code for TaskCall execution by wrapping it with input handling.
        """
        # Escape the input contents for Scala string literal
        escaped_input = input_contents.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
        
        # Remove any existing object Main wrapper from the generated code
        clean_code = code.strip()
        if "object Main" in clean_code:
            # Extract just the function definition from inside the object
            # This is a simple approach - could be made more robust if needed
            import_match = re.search(r'^(import .*\n)*', clean_code)
            imports = import_match.group(0) if import_match else ""
            func_match = re.search(r'def example\([^)]*\)[^{]*\{.*\}', clean_code, re.DOTALL)
            if func_match:
                clean_code = imports + func_match.group(0)
        
        # Place the generated function inside the Main object
        wrapped_code = f"""
object Main {{
  def main(args: Array[String]): Unit = {{
    val input = "{escaped_input}"
    val result = example(input)
    println(result)
  }}
  
  {clean_code.strip()}
}}
"""
        return self.prepare_codebase(wrapped_code)


# Create singleton instance
scala_utils = ScalaUtils()

# Export backward-compatible functions
prepare_codebase = scala_utils.prepare_codebase
query_code = scala_utils.query_code
run_scala_check = scala_utils.run_validation
run_scala_project_with_output = scala_utils.run_script