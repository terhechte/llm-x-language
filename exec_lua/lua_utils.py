import os
import subprocess
import logging
from typing import List, Optional, Tuple

from base_executor import BaseLanguageUtils
from utils import Result, find_code_blocks_with_language


class LuaUtils(BaseLanguageUtils):
    """Lua-specific language utilities."""
    
    def __init__(self, use_docker: bool = False):
        super().__init__(
            language="Lua",
            template_name="lua_container",
            main_file="main.lua",
            use_docker=use_docker
        )
    
    def get_language_aliases(self) -> List[str]:
        """Return Lua language aliases."""
        return ["lua"]
    
    
    def query_code(self, prompt: str, model: str) -> Optional[Tuple[str, str, int, int]]:
        """
        Query the LLM for Lua code based on the prompt.
        Special handling for Lua - returns the full response as code.
        """
        from llm import request
        response, prompt_tokens, completion_tokens = request(prompt, model, self.language)
        logging.debug(response)
        logging.debug("--------------------------------")
        if not response:
            return None
        
        # For Lua, the original implementation returns the full response as code
        # This might be because Lua tasks expect plain text responses
        # Let's check for code blocks first, and fall back to full response
        code_blocks = find_code_blocks_with_language(response)
        lua_code = self.extract_language_code(code_blocks)
        
        # If no code blocks found, use the full response
        if not lua_code:
            lua_code = response
        
        logging.debug(lua_code)
        return lua_code, response, prompt_tokens, completion_tokens
    
    def run_validation(self, code_path: str) -> Result:
        """Run luac -p to check Lua code for syntax errors."""
        try:
            lua_file = os.path.join(code_path, self.main_file)
            result = subprocess.run(
                ["luac", "-p", lua_file],
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode != 0:
                return Result(success=False, errors=[result.stderr.strip()])
            return Result(success=True, errors=[])
        except subprocess.CalledProcessError as e:
            return Result(success=False, errors=[str(e)])
        except Exception as e:
            return Result(success=False, errors=[f"Error running lua check: {str(e)}"])
    
    def get_run_command(self) -> List[str]:
        """Get command to run Lua code."""
        # Use /bin/sh to avoid requiring bash in alpine base image.
        # Set up LuaRocks paths if available, then execute main.lua.
        return [
            "sh",
            "-lc",
            "if command -v luarocks >/dev/null 2>&1; then eval $(luarocks path); fi; lua main.lua",
        ]
    
    def get_validation_command(self) -> Optional[List[str]]:
        """Get command to validate Lua code."""
        return ["luac", "-p", "main.lua"]
    
    def get_build_command(self) -> Optional[List[str]]:
        """Lua doesn't need a build step."""
        return None
    
    def extract_runtime_errors(self, stdout: str, stderr: str) -> List[str]:
        """Extract Lua-specific runtime errors."""
        if stderr:
            return [stderr.strip()]
        return ["Runtime error occurred"]
    
    def prepare_codebase_for_call(self, code: str, input_contents: str) -> str:
        """
        Prepare Lua code for TaskCall execution by wrapping it with input handling.
        """
        # For Lua, use [[ ]] for multi-line strings or escape quotes
        # Check if input contains ]] which would break [[ ]] syntax
        if ']]' in input_contents:
            # Use regular string with escaping
            escaped_input = (input_contents
                .replace('\\', '\\\\')
                .replace('"', '\\"')
                .replace('\n', '\\n')
                .replace('\r', '\\r')
                .replace('\t', '\\t'))
            input_literal = f'"{escaped_input}"'
        else:
            # Use [[ ]] for cleaner multi-line strings
            input_literal = f'[[{input_contents}]]'
        
        # For Lua, we need to add code to parse input and call the function
        wrapped_code = f"""
{code.strip()}

-- Main execution
local input = {input_literal}
local result = example(input)
print(result)
"""
        return super().prepare_codebase(wrapped_code)


# Create singleton instance
lua_utils = LuaUtils()

# Export backward-compatible functions
prepare_codebase = lua_utils.prepare_codebase
query_code = lua_utils.query_code
run_lua_check = lua_utils.run_validation
run_lua_script = lua_utils.run_script
