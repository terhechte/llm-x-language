import os
import subprocess
import logging
import json
from typing import List, Optional, Tuple

from base_executor import BaseLanguageUtils
from utils import Result

class CSharpUtils(BaseLanguageUtils):
    """C#-specific language utilities."""

    def __init__(self, use_docker: bool = False):
        super().__init__(
            language="CSharp",
            template_name="csharp_container",
            main_file="Program.cs",
            use_docker=use_docker,
        )

    def get_language_aliases(self) -> List[str]:
        """Return C# language aliases."""
        return ["csharp", "cs", "c#"]

    def extract_language_code(self, code_blocks: List[Tuple[str, str]]) -> str:
        """
        Extract C# code blocks with special handling.
        """
        # Extract matching code blocks
        aliases = self.get_language_aliases()
        matching_code = []
        for lang, code in code_blocks:
            if lang.lower() in aliases:
                matching_code.append(code)

        csharp_code = "\n".join(matching_code)

        # Add using statements if missing common ones
        if csharp_code:
            # Check for top-level program or traditional class structure
            has_namespace = "namespace " in csharp_code
            has_class = "class " in csharp_code
            has_main = "Main(" in csharp_code or "Main (" in csharp_code
            
            # Add common using statements if not present
            using_statements = []
            if "using System;" not in csharp_code and not has_namespace:
                using_statements.append("using System;")
            if "using System.Text.Json;" not in csharp_code and "JsonSerializer" in csharp_code:
                using_statements.append("using System.Text.Json;")
            if "using Microsoft.AspNetCore" not in csharp_code and ("WebApplication" in csharp_code or "app.MapGet" in csharp_code):
                using_statements.append("using Microsoft.AspNetCore.Builder;")
                using_statements.append("using Microsoft.AspNetCore.Http;")
            
            if using_statements:
                csharp_code = "\n".join(using_statements) + "\n\n" + csharp_code

        return csharp_code

    def run_validation(self, code_path: str) -> Result:
        """Run dotnet build for code validation."""
        errors = []
        try:
            result = subprocess.run(
                ["dotnet", "build", "--nologo", "--verbosity", "quiet"],
                cwd=code_path,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.stderr:
                # Parse C# compiler errors
                for line in result.stderr.split("\n"):
                    if line.strip() and ("error " in line or "Error " in line):
                        errors.append(line.strip())
            
            if result.stdout:
                # Check stdout for errors too
                for line in result.stdout.split("\n"):
                    if line.strip() and ("error " in line or "Error " in line):
                        errors.append(line.strip())

            return Result(success=result.returncode == 0, errors=errors)

        except subprocess.SubprocessError as e:
            logging.error("Error during dotnet build: %s", e)
            return Result(success=False, errors=[str(e)])

    def get_run_command(self) -> List[str]:
        """Get command to run C# code."""
        return ["dotnet", "run"]

    def get_build_command(self) -> Optional[List[str]]:
        """Get the build command for C#."""
        return ["dotnet", "build", "--nologo"]

    def extract_build_errors(self, stdout: str, stderr: str) -> List[str]:
        """Extract C#-specific build errors."""
        errors = []
        if stderr and ("error " in stderr or "Error " in stderr):
            errors.append(stderr)
        if stdout and ("error " in stdout or "Error " in stdout):
            errors.append(stdout)
        return errors if errors else ["Build failed"]

    def extract_runtime_errors(self, stdout: str, stderr: str) -> List[str]:
        """Extract C#-specific runtime errors."""
        if stderr:
            # Filter out NuGet warnings, focus on actual errors
            if "Exception" in stderr or ("error" in stderr.lower() and "warning NU" not in stderr):
                return [stderr]
        return ["Runtime error occurred"]
    
    def clean_output(self, output: str) -> str:
        """Clean C# output by removing NuGet warnings."""
        output_lines = []
        for line in output.split('\n'):
            if not line.strip().startswith('/app/csharp_container.csproj : warning NU'):
                output_lines.append(line)
        return '\n'.join(output_lines).strip()

    def run_script(self, code_path: str, timeout: int = 60) -> Result:
        """
        Runs the C# project and returns its output.
        """
        try:
            # First build the project
            build_result = subprocess.run(
                ["dotnet", "build", "--nologo", "--verbosity", "quiet"],
                cwd=code_path,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            
            if build_result.returncode != 0:
                logging.error("Build failed: %s", build_result.stderr)
                return Result(success=False, errors=[build_result.stderr])

            # Then run it
            result = subprocess.run(
                ["dotnet", "run", "--no-build", "--no-logo"],
                cwd=code_path,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )

            if result.stderr:
                logging.debug("Raw Err Output: %s", result.stderr)
                if "Exception" in result.stderr or "error" in result.stderr.lower():
                    return Result(success=False, errors=[result.stderr])

            # Clean the output
            clean_output = self.clean_output(result.stdout)

            logging.debug("Raw Output: %s", result.stdout)
            return Result(success=True, errors=[], output=clean_output)

        except subprocess.TimeoutExpired:
            logging.error(f"C# project execution timed out after {timeout} seconds")
            return Result(
                success=False, errors=[f"Execution timed out after {timeout} seconds"]
            )
        except subprocess.SubprocessError as e:
            logging.error("Error running C# project: %s", e)
            return Result(success=False, errors=[str(e)])

    def prepare_codebase(self, code: str) -> str:
        """
        Override prepare_codebase to ensure C# code has proper structure.
        """
        # Check if code is a top-level program or needs a class wrapper
        has_namespace = "namespace " in code
        has_class = "class " in code and "Program" in code
        has_main = "static void Main" in code or "static async Task Main" in code
        
        # If it's not a complete program, assume it's top-level statements
        if not has_namespace and not has_class and not has_main:
            # Modern C# supports top-level programs, so we can use the code as-is
            pass
        elif has_class and not has_main:
            # If there's a class but no Main method, add one
            code = code.strip() + """

public static class Program
{
    public static void Main(string[] args)
    {
        // Entry point added for execution
    }
}
"""
        
        return super().prepare_codebase(code)

    def prepare_codebase_for_call(self, code: str, input_contents: str) -> str:
        """
        Prepare C# code for TaskCall execution by wrapping it with input handling.
        """
        import re
        
        # Escape the input for C# string literal
        # Use verbatim string literals with @ prefix to handle quotes and newlines
        escaped_input = input_contents.replace('"', '""')
        
        clean_code = code.strip()
        
        # Check if the LLM generated a class with the example method
        class_match = re.search(r'(?:public\s+)?(?:static\s+)?class\s+(\w+)', clean_code)
        has_utility_class = class_match and class_match.group(1) not in ['Program', 'Main']
        
        if has_utility_class:
            # The LLM generated a separate class (like StringUtilities)
            class_name = class_match.group(1)
            
            # Remove any existing using System; to avoid duplicates
            clean_code_no_using = clean_code
            if "using System;" in clean_code:
                clean_code_no_using = clean_code.replace("using System;", "").strip()
            
            # Use top-level statements to call the class method
            # This must come BEFORE the class declaration in C#
            wrapped_code = f'''
using System;

// Main execution (top-level statements must come first)
var input = @"{escaped_input}";
var result = {class_name}.example(input);
Console.WriteLine(result);

{clean_code_no_using}
'''
        else:
            # Check if it's just a method without a class
            has_static_method = "public static" in clean_code or "static string" in clean_code
            has_class = "class " in clean_code
            
            if has_static_method and not has_class:
                # Wrap the static method in a Program class
                wrapped_code = f'''
using System;

public class Program
{{
    {clean_code}
    
    public static void Main(string[] args)
    {{
        var input = @"{escaped_input}";
        var result = example(input);
        Console.WriteLine(result);
    }}
}}
'''
            else:
                # For code that already has proper structure
                wrapped_code = f'''
using System;

{clean_code}

public class Program
{{
    public static void Main(string[] args)
    {{
        var input = @"{escaped_input}";
        var result = example(input);
        Console.WriteLine(result);
    }}
}}
'''
        return self.prepare_codebase(wrapped_code)
    
    def run_docker_script(self, code_path: str, timeout: int = 60, port: Optional[int] = None) -> Result:
        """Override to clean C# output from Docker."""
        result = super().run_docker_script(code_path, timeout, port)
        if result.success and result.output:
            result.output = self.clean_output(result.output)
        return result


# Create singleton instance
csharp_utils = CSharpUtils()

# Export backward-compatible functions
prepare_codebase = csharp_utils.prepare_codebase
query_code = csharp_utils.query_code
run_csharp_check = csharp_utils.run_validation
run_csharp_project_with_output = csharp_utils.run_script