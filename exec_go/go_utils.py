import os
import subprocess
import logging
import shutil
from typing import List, Optional

from base_executor import BaseLanguageUtils
from utils import Result


class GoUtils(BaseLanguageUtils):
    """Go-specific language utilities."""
    
    def __init__(self):
        super().__init__(
            language="Go",
            template_name="go_container",
            main_file="main.go"
        )
    
    def get_language_aliases(self) -> List[str]:
        """Return Go language aliases."""
        return ["go", "golang"]
    
    def prepare_codebase_for_call(self, code: str, input_contents: str) -> str:
        """
        Prepare Go code for TaskCall execution by wrapping it with input handling.
        """
        # Check if code already has package declaration
        if "package main" in code:
            # If it has package main, check for main function
            if "func main()" in code:
                # Code has main function, use as-is
                return self.prepare_codebase(code)
            else:
                # The AI should provide all necessary imports
                # We just add the main function
                wrapped_code = f"""{code.strip()}

func main() {{
    input := `{input_contents}`
    result := example(input)
    // The AI should have imported fmt if it needs println
    // Otherwise it might use a different output method
    println(result)
}}
"""
        else:
            # No package declaration - the AI should provide complete code
            # Let's add minimal wrapper
            wrapped_code = f"""package main

{code.strip()}

func main() {{
    input := `{input_contents}`
    result := example(input)
    println(result)
}}
"""
        return self.prepare_codebase(wrapped_code)
    
    def run_validation(self, code_path: str) -> Result:
        """Run goimports to fix formatting/imports and go vet to check for errors."""
        errors = []
        
        # First check if goimports is available, fall back to gofmt if not
        goimports_available = shutil.which("goimports") is not None
        
        if goimports_available:
            # Run goimports -w to fix formatting and organize imports
            try:
                result = subprocess.run(
                    ["goimports", "-w", "main.go"],
                    cwd=code_path,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                
                # goimports -w doesn't produce output on success, only on error
                if result.stderr:
                    errors.append(f"goimports error: {result.stderr}")
            except subprocess.SubprocessError as e:
                logging.error("Error during goimports fix: %s", e)
                errors.append(f"goimports error: {str(e)}")
        else:
            # Fall back to gofmt if goimports not available
            try:
                result = subprocess.run(
                    ["gofmt", "-w", "main.go"],
                    cwd=code_path,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                
                if result.stderr:
                    errors.append(f"gofmt error: {result.stderr}")
            except subprocess.SubprocessError as e:
                logging.error("Error during gofmt fix: %s", e)
                errors.append(f"gofmt error: {str(e)}")
        
        # Then run go vet for static analysis
        try:
            result = subprocess.run(
                ["go", "vet", "./..."],
                cwd=code_path,
                capture_output=True,
                text=True,
                check=False,
            )
            
            if result.stderr:
                errors.append(f"go vet errors: {result.stderr}")
            
            if result.returncode != 0 and not result.stderr:
                errors.append("go vet failed")
                
        except subprocess.SubprocessError as e:
            logging.error("Error during go vet check: %s", e)
            errors.append(f"go vet error: {str(e)}")
        
        return Result(success=len(errors) == 0, errors=errors)
    
    def get_run_command(self) -> List[str]:
        """Get command to run Go code."""
        return ["go", "run", "main.go"]
    
    def get_build_command(self) -> Optional[List[str]]:
        """Get the build command for Go."""
        return ["go", "build", "-o", "main", "main.go"]
    
    def extract_build_errors(self, stdout: str, stderr: str) -> List[str]:
        """Extract Go-specific build errors."""
        errors = []
        
        # Go outputs errors to stderr
        if stderr:
            # Parse Go error format (file:line:column: message)
            for line in stderr.split('\n'):
                if line.strip() and '.go:' in line:
                    errors.append(line.strip())
                elif line.strip() and 'error:' in line.lower():
                    errors.append(line.strip())
        
        # Sometimes errors appear in stdout too
        if stdout and 'error' in stdout.lower():
            for line in stdout.split('\n'):
                if line.strip() and '.go:' in line:
                    errors.append(line.strip())
        
        return errors if errors else ["Build failed"]
    
    def extract_runtime_errors(self, stdout: str, stderr: str) -> List[str]:
        """Extract Go-specific runtime errors."""
        errors = []
        
        if stderr:
            # Look for panic messages or runtime errors
            if 'panic:' in stderr or 'runtime error:' in stderr:
                errors.append(stderr)
            else:
                errors.append(f"Runtime error: {stderr}")
        
        return errors if errors else ["Runtime error occurred"]


# Create singleton instance
go_utils = GoUtils()

# Export backward-compatible functions
prepare_codebase = go_utils.prepare_codebase
query_code = go_utils.query_code
run_go_check = go_utils.run_validation
run_go_script = go_utils.run_script