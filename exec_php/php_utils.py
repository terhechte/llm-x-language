import os
import subprocess
import logging
from typing import List, Optional

from base_executor import BaseLanguageUtils
from utils import Result


class PHPUtils(BaseLanguageUtils):
    """PHP-specific language utilities."""
    
    def __init__(self):
        super().__init__(
            language="PHP",
            template_name="php_container",
            main_file="main.php"
        )
    
    def get_language_aliases(self) -> List[str]:
        """Return PHP language aliases."""
        return ["php"]
    
    def run_validation(self, code_path: str) -> Result:
        """Run PHP syntax check."""
        try:
            result = subprocess.run(
                ["php", "-l", os.path.join(code_path, "main.php")],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                return Result(success=True, errors=[])
            
            errors = []
            if result.stderr:
                errors = [line for line in result.stderr.split('\n') if line.strip()]
            
            return Result(success=False, errors=errors)
        except subprocess.SubprocessError as e:
            logging.error("Error during PHP syntax check: %s", e)
            return Result(success=False, errors=[str(e)])
    
    def get_run_command(self) -> List[str]:
        """Get command to run PHP code."""
        return ["php", "main.php"]
    
    def get_build_command(self) -> Optional[List[str]]:
        """PHP doesn't need a build step."""
        return None
    
    def extract_runtime_errors(self, stdout: str, stderr: str) -> List[str]:
        """Extract PHP-specific runtime errors."""
        if stderr:
            return [stderr]
        return ["Runtime error occurred"]
    
    def prepare_codebase_for_call(self, code: str, input_contents: str) -> str:
        """
        Prepare PHP code for TaskCall execution by wrapping it with input handling.
        """
        # For PHP, we need to add code to parse input and call the function
        wrapped_code = f"""<?php
{code.strip().replace('<?php', '').replace('?>', '')}

// Main execution
$input = '{input_contents}';
$result = example($input);
echo $result;
?>"""
        return self.prepare_codebase(wrapped_code)


# Create singleton instance
php_utils = PHPUtils()

# Export backward-compatible functions
prepare_codebase = php_utils.prepare_codebase
query_code = php_utils.query_code
run_php_check = php_utils.run_validation
run_php_script = php_utils.run_script