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
                ["dotnet", "build", "--nologo", "--verbosity", "quiet", "/p:WarningLevel=0", "/p:NoWarn=NU1903"],
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
        return ["dotnet", "run", "--nologo", "--verbosity", "quiet", "/p:NoWarn=NU1903"]
    
    def get_validation_command(self) -> Optional[List[str]]:
        """Get command to validate C# code."""
        return ["dotnet", "build", "--no-restore"]

    def get_build_command(self) -> Optional[List[str]]:
        """Get the build command for C#."""
        return ["dotnet", "build", "--nologo", "--verbosity", "quiet", "/p:WarningLevel=0", "/p:NoWarn=NU1903"]

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
        """Clean C# output by removing build output, warnings, and other noise."""
        output_lines = []
        skip_patterns = [
            # Build output patterns
            'Build succeeded',
            'Time Elapsed',
            'Warning(s)',
            'Error(s)',
            # NuGet warnings
            '/app/csharp_container.csproj : warning NU',
            # CS warnings (compiler warnings)
            ': warning CS',
            # General warning lines
            'warning',
            # Restore messages
            'Determining projects to restore',
            'Restored',
            'All projects are up-to-date',
        ]
        
        for line in output.split('\n'):
            line_stripped = line.strip()
            # Skip empty lines
            if not line_stripped:
                continue
            # Skip lines matching any skip pattern
            should_skip = False
            for pattern in skip_patterns:
                if pattern.lower() in line_stripped.lower():
                    should_skip = True
                    break
            if not should_skip:
                output_lines.append(line)
        
        return '\n'.join(output_lines).strip()

    def run_script(self, code_path: str, timeout: int = 60) -> Result:
        """
        Runs the C# project and returns its output.
        """
        try:
            # First build the project
            build_result = subprocess.run(
                ["dotnet", "build", "--nologo", "--verbosity", "quiet", "/p:WarningLevel=0", "/p:NoWarn=NU1903"],
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
                ["dotnet", "run", "--no-build", "--nologo", "--verbosity", "quiet", "/p:NoWarn=NU1903"],
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
        import re
        
        # Check what structure the code has using more robust regex patterns
        has_namespace = bool(re.search(r'^\s*namespace\s+\w+', code, re.MULTILINE))
        
        # More robust Program class detection
        program_class_pattern = r'^\s*(public\s+)?(static\s+)?(partial\s+)?class\s+Program\s*(\s*:\s*[\w\s,]+)?\s*\{'
        has_program_class = bool(re.search(program_class_pattern, code, re.MULTILINE))
        
        # More robust Main method detection
        main_method_pattern = r'^\s*(public\s+)?static\s+(async\s+)?(Task|void)\s+Main\s*\('
        has_main = bool(re.search(main_method_pattern, code, re.MULTILINE))
        
        has_any_class = bool(re.search(r'^\s*(public\s+)?(static\s+)?(partial\s+)?class\s+', code, re.MULTILINE))
        
        # Check for custom utility classes (like StringUtilities)
        class_match = re.search(r'^\s*(?:public\s+)?(?:static\s+)?(?:partial\s+)?class\s+(\w+)', code, re.MULTILINE)
        has_utility_class = class_match and class_match.group(1) not in ['Program', 'Main']
        
        # Split code into using statements and the rest
        code_lines = code.strip().split('\n')
        usings = []
        body_lines = []
        
        for line in code_lines:
            line_stripped = line.strip()
            if line_stripped.startswith('using ') and line_stripped.endswith(';'):
                usings.append(line)
            else:
                body_lines.append(line)
        
        # Build using section
        using_section = '\n'.join(usings) + '\n\n' if usings else ''
        body_code = '\n'.join(body_lines).strip()
        
        # Decide how to structure the code
        if has_program_class and has_main:
            # Already has proper structure
            logging.debug("C#: Program class with Main method detected, using code as-is")
            return super().prepare_codebase(code)
        elif has_utility_class and not has_main:
            # Has a utility class but no Main - use top-level statements
            # This is valid modern C# where top-level statements come before class declarations
            wrapped_code = f"""{using_section}// Top-level program entry point
Console.WriteLine("Program ready");

{body_code}
"""
        elif has_any_class and not has_main and not has_utility_class:
            # Has some class but it's not a utility class and no Main
            # Add a Program class with Main
            wrapped_code = f"""{using_section}{body_code}

public static class Program
{{
    public static void Main(string[] args)
    {{
        // Entry point added for execution
    }}
}}
"""
        elif not has_any_class and not has_main:
            # Just loose methods or code - wrap in Program class
            if body_code:
                # Check if it looks like methods that should be in a class
                has_methods = "public " in body_code or "private " in body_code or "static " in body_code or "void " in body_code or "string " in body_code or "int " in body_code
                
                if has_methods:
                    # Wrap methods in Program class
                    # Indent the body code
                    indented_body = '\n'.join('    ' + line if line.strip() else '' 
                                            for line in body_code.split('\n'))
                    wrapped_code = f"""{using_section}public static class Program
{{
{indented_body}
    
    public static void Main(string[] args)
    {{
        // Entry point added for execution
    }}
}}
"""
                else:
                    # Looks like top-level statements, use as-is
                    wrapped_code = code
            else:
                # Empty or minimal code, create basic structure
                wrapped_code = f"""{using_section}Console.WriteLine("Program ready");
"""
        else:
            # Default case - use code as-is
            wrapped_code = code
        
        return super().prepare_codebase(wrapped_code)

    def prepare_codebase_for_call(self, code: str, input_contents: str) -> str:
        """
        Prepare C# code for TaskCall execution by wrapping it with input handling.
        """
        import re
        
        # Escape the input for C# string literal
        # Use verbatim string literals with @ prefix to handle quotes and newlines
        escaped_input = input_contents.replace('"', '""')
        
        clean_code = code.strip()
        
        # Remove all using statements from the generated code to avoid placement issues
        # We'll add them at the top of the file properly
        lines = clean_code.split('\n')
        code_without_usings = []
        for line in lines:
            # Skip using statements and empty lines after them
            if line.strip().startswith('using ') and line.strip().endswith(';'):
                continue
            # Keep all other lines
            code_without_usings.append(line)
        
        # Join and clean up extra blank lines
        clean_code_no_using = '\n'.join(code_without_usings).strip()
        
        # Check if the LLM generated a class with the example method
        class_match = re.search(r'(?:public\s+)?(?:static\s+)?class\s+(\w+)', clean_code_no_using)
        has_utility_class = class_match and class_match.group(1) not in ['Program', 'Main']
        
        # Standard imports that cover most common needs
        imports = """using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;"""
        
        # Add JSON imports if needed
        if "JsonSerializer" in clean_code or "JsonElement" in clean_code:
            imports += "\nusing System.Text.Json;"
        
        if has_utility_class:
            # The LLM generated a separate class (like StringUtilities)
            class_name = class_match.group(1)
            
            # Use top-level statements to call the class method
            # This must come BEFORE the class declaration in C#
            wrapped_code = f'''{imports}

// Main execution (top-level statements must come first)
var input = @"{escaped_input}";
var result = {class_name}.example(input);
Console.WriteLine(result);

{clean_code_no_using}
'''
        else:
            # Check if it's just a method without a class
            has_static_method = "public static" in clean_code_no_using or "static string" in clean_code_no_using
            has_class = "class " in clean_code_no_using
            
            if has_static_method and not has_class:
                # Wrap the static method in a Program class
                wrapped_code = f'''{imports}

public class Program
{{
    {clean_code_no_using}
    
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
                wrapped_code = f'''{imports}

{clean_code_no_using}

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