"""Base executor utilities for all language-specific executors."""

import os
import subprocess
import time
import json
import logging
import threading
from typing import Optional, Tuple, List, Any, Dict
from abc import ABC, abstractmethod
import requests

from llm import request
from utils import find_code_blocks_with_language, Result, TaskResult, ProcessManager, wait_for_server_ready, are_json_values_equal, are_string_values_equal, ContainsMatch
from task import TaskCall, TaskRun, TaskCheck, TaskContains
from docker_utils import port_manager, build_docker_run_command


class BaseLanguageUtils(ABC):
    """Base class for language-specific utilities."""
    
    def __init__(self, language: str, template_name: str, main_file: str, use_docker: bool = False):
        """
        Initialize base language utilities.
        
        Args:
            language: Programming language name
            template_name: Name of the container template directory
            main_file: Main file name within the container
            use_docker: Whether to use Docker for execution (default: False)
        """
        self.language = language
        self.template_name = template_name
        self.main_file = main_file
        self.template_path = os.path.join(os.path.dirname(__file__), template_name)
        self.template_dest = os.path.join(os.path.dirname(__file__), "dojo", template_name)
        self.use_docker = use_docker or os.environ.get('LLM_BENCHMARK_USE_DOCKER', '').lower() == 'true'
        self.docker_image = f"llm-benchmark/{language.lower()}"
        self.allocated_port = None
    
    def prepare_codebase(self, code: str) -> str:
        """
        Prepares the codebase by writing the code to the main file in the template directory.
        """
        try:
            main_file_path = os.path.join(self.template_dest, self.main_file)
            os.makedirs(os.path.dirname(main_file_path), exist_ok=True)
            with open(main_file_path, "w", encoding="utf-8") as f:
                f.write(code)
                f.flush()
                os.fsync(f.fileno())  # Force write to disk
            return self.template_dest
        except IOError as e:
            logging.error(f"Failed to write {self.language} code to {self.main_file}: {e}")
            raise
    
    def query_code(self, prompt: str, model: str) -> Optional[Tuple[str, str, int, int]]:
        """
        Queries the LLM for code based on the prompt.
        Returns a tuple of (code, response, prompt_tokens, completion_tokens) or None if the query fails.
        """
        response, prompt_tokens, completion_tokens = request(prompt, model, self.language)
        logging.debug(response)
        logging.debug("--------------------------------")
        if not response:
            return None
        
        code_blocks = find_code_blocks_with_language(response)
        
        # Extract code for this language
        language_code = self.extract_language_code(code_blocks)
        
        logging.debug(language_code)
        return language_code, response, prompt_tokens, completion_tokens
    
    def extract_language_code(self, code_blocks: List[Tuple[str, str]]) -> str:
        """
        Extract code blocks for this specific language.
        Can be overridden for language-specific behavior.
        """
        # Get language-specific aliases
        aliases = self.get_language_aliases()
        
        # Extract matching code blocks
        matching_code = []
        for lang, code in code_blocks:
            if lang.lower() in aliases:
                matching_code.append(code)
        
        return "\n".join(matching_code)
    
    @abstractmethod
    def get_language_aliases(self) -> List[str]:
        """Return list of language aliases (e.g., ['python', 'py'])."""
        pass
    
    @abstractmethod
    def run_validation(self, code_path: str) -> Result:
        """
        Run language-specific validation/linting/type-checking.
        Returns a Result object with success status and any errors found.
        """
        pass
    
    def run_validation_wrapper(self, code_path: str) -> Result:
        """Wrapper that chooses between Docker and native validation."""
        if self.use_docker:
            return self.run_docker_validation(code_path)
        else:
            return self.run_validation(code_path)
    
    @abstractmethod
    def get_run_command(self) -> List[str]:
        """Get the command to run the main file."""
        pass
    
    def get_build_command(self) -> Optional[List[str]]:
        """Get the build command if needed. Return None if no build step required."""
        return None
    
    def run_build(self, code_path: str) -> Result:
        """
        Run the build command if needed.
        """
        build_cmd = self.get_build_command()
        if not build_cmd:
            return Result(success=True, errors=[])
        
        try:
            result = subprocess.run(
                build_cmd,
                cwd=code_path,
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
            
            if result.returncode != 0:
                errors = self.extract_build_errors(result.stdout, result.stderr)
                return Result(success=False, errors=errors)
            
            return Result(success=True, errors=[])
        except subprocess.TimeoutExpired:
            return Result(success=False, errors=["Build timed out after 60 seconds"])
        except subprocess.SubprocessError as e:
            return Result(success=False, errors=[str(e)])
    
    def run_build_wrapper(self, code_path: str) -> Result:
        """Wrapper that chooses between Docker and native build."""
        if self.use_docker:
            return self.run_docker_build(code_path)
        else:
            return self.run_build(code_path)
    
    def extract_build_errors(self, stdout: str, stderr: str) -> List[str]:
        """
        Extract meaningful error messages from build output.
        Can be overridden for language-specific error extraction.
        """
        errors = []
        if stderr:
            errors.append(stderr)
        if stdout and "error" in stdout.lower():
            errors.append(stdout)
        return errors if errors else ["Build failed"]
    
    def run_script(self, code_path: str, timeout: int = 60) -> Result:
        """
        Runs the script and returns its output.
        """
        try:
            cmd = self.get_run_command()
            result = subprocess.run(
                cmd,
                cwd=code_path,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
            
            if result.stderr:
                logging.debug("Raw Err Output: %s", result.stderr)
                errors = self.extract_runtime_errors(result.stdout, result.stderr)
                return Result(success=False, errors=errors)
            
            logging.debug("Raw Output: %s", result.stdout)
            return Result(success=True, errors=[], output=result.stdout)
            
        except subprocess.TimeoutExpired:
            logging.error(f"{self.language} script execution timed out after {timeout} seconds")
            return Result(success=False, errors=[f"Execution timed out after {timeout} seconds"])
        except subprocess.SubprocessError as e:
            logging.error(f"Error running {self.language} script: %s", e)
            return Result(success=False, errors=[str(e)])
    
    def run_script_wrapper(self, code_path: str, timeout: int = 60, port: Optional[int] = None) -> Result:
        """Wrapper that chooses between Docker and native script execution."""
        if self.use_docker:
            return self.run_docker_script(code_path, timeout, port)
        else:
            return self.run_script(code_path, timeout)
    
    def extract_runtime_errors(self, stdout: str, stderr: str) -> List[str]:
        """
        Extract meaningful runtime error messages.
        Can be overridden for language-specific error extraction.
        """
        return [stderr] if stderr else ["Runtime error occurred"]
    
    def get_docker_command(self, base_command: List[str], port: Optional[int] = None) -> List[str]:
        """
        Build Docker command for executing code.
        
        Args:
            base_command: The base command to run in the container
            port: Optional port to expose for HTTP server tests
            
        Returns:
            Complete docker run command
        """
        volume_mount = f"{os.path.abspath(self.template_dest)}:/app"
        
        return build_docker_run_command(
            image=self.docker_image,
            volume_mount=volume_mount,
            command=base_command,
            port=port,
            container_name=f"{self.language.lower()}-{os.getpid()}-{threading.get_ident()}"
        )
    
    def run_docker_validation(self, code_path: str) -> Result:
        """Run validation using Docker."""
        # For Docker, we don't need to run validation separately
        # as dependencies are pre-installed in the image
        return Result(success=True, errors=[])
    
    def run_docker_build(self, code_path: str) -> Result:
        """Run build command using Docker if needed."""
        build_cmd = self.get_build_command()
        if not build_cmd:
            return Result(success=True, errors=[])
        
        try:
            docker_cmd = self.get_docker_command(build_cmd)
            result = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=120,  # Longer timeout for Docker
                check=False,
            )
            
            if result.returncode != 0:
                errors = self.extract_build_errors(result.stdout, result.stderr)
                return Result(success=False, errors=errors)
            
            return Result(success=True, errors=[])
        except subprocess.TimeoutExpired:
            return Result(success=False, errors=["Docker build timed out after 120 seconds"])
        except subprocess.SubprocessError as e:
            return Result(success=False, errors=[str(e)])
    
    def run_docker_script(self, code_path: str, timeout: int = 60, port: Optional[int] = None) -> Result:
        """Run script using Docker."""
        try:
            cmd = self.get_run_command()
            docker_cmd = self.get_docker_command(cmd, port)
            
            result = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=timeout + 10,  # Add buffer for Docker overhead
                check=False,
            )
            
            if result.stderr and result.returncode != 0:
                logging.debug("Docker Raw Err Output: %s", result.stderr)
                errors = self.extract_runtime_errors(result.stdout, result.stderr)
                return Result(success=False, errors=errors)
            
            logging.debug("Docker Raw Output: %s", result.stdout)
            return Result(success=True, errors=[], output=result.stdout)
            
        except subprocess.TimeoutExpired:
            logging.error(f"Docker {self.language} script execution timed out after {timeout} seconds")
            return Result(success=False, errors=[f"Docker execution timed out after {timeout} seconds"])
        except subprocess.SubprocessError as e:
            logging.error(f"Error running Docker {self.language} script: %s", e)
            return Result(success=False, errors=[str(e)])
    
    def prepare_codebase_for_call(self, code: str, input_contents: str) -> str:
        """
        Prepare code for TaskCall execution.
        Default implementation just uses prepare_codebase.
        Can be overridden for language-specific handling.
        """
        return self.prepare_codebase(code)
    
    def get_mutated_code(self, code_path: str) -> str:
        """
        Read the mutated code from the prepared codebase.
        """
        try:
            main_file_path = os.path.join(code_path, self.main_file)
            with open(main_file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logging.error(f"Failed to read mutated code: {e}")
            return ""


# Common task execution functions that use the language utilities

def exec_run_common(task: TaskRun, model: str, run: int, utils: BaseLanguageUtils) -> TaskResult:
    """
    Common implementation for executing a TaskRun.
    """
    process_manager = ProcessManager()
    allocated_port = None
    
    try:
        r = utils.query_code(task.prompt, model)
    except (ValueError, RuntimeError, TimeoutError) as e:
        return TaskResult.error(run, [str(e)])
    if not r:
        return TaskResult(
            run=run,
            success=False,
            errors=["Failed to query code"],
            response="",
            code="",
            output="",
            expected_output=task.expected_output,
            tokens=(0, 0),
            mutated_code="",
        )
    code, response, prompt_tokens, completion_tokens = r
    
    code_path = utils.prepare_codebase(code)
    
    # Read the mutated code from the file
    mutated_code = utils.get_mutated_code(code_path) if code_path else ""
    
    if not code_path:
        return TaskResult(
            run=run,
            success=False,
            errors=["Failed to prepare codebase"],
            response=response,
            code=code,
            output="",
            expected_output=task.expected_output,
            tokens=(prompt_tokens, completion_tokens),
            mutated_code=mutated_code,
        )
    
    # Run validation
    result = utils.run_validation_wrapper(code_path)
    if not result.success:
        return TaskResult(
            run=run,
            success=False,
            errors=result.errors,
            response=response,
            code=code,
            output="",
            expected_output=task.expected_output,
            tokens=(prompt_tokens, completion_tokens),
            mutated_code=mutated_code,
        )
    
    # Build if needed
    result = utils.run_build_wrapper(code_path)
    if not result.success:
        return TaskResult(
            run=run,
            success=False,
            errors=result.errors,
            response=response,
            code=code,
            output="",
            expected_output=task.expected_output,
            tokens=(prompt_tokens, completion_tokens),
            mutated_code=mutated_code,
        )
    
    # Handle Docker vs native execution for HTTP server
    if utils.use_docker:
        # Allocate a port for Docker
        allocated_port = port_manager.allocate_port()
        if not allocated_port:
            return TaskResult(
                run=run,
                success=False,
                errors=["Failed to allocate port for Docker container"],
                response=response,
                code=code,
                output="",
                expected_output=task.expected_output,
                tokens=(prompt_tokens, completion_tokens),
                mutated_code=mutated_code,
            )
        
        # Update the request URL with the allocated port
        import re
        original_port = re.search(r':(\d+)', task.request)
        if original_port:
            test_url = task.request.replace(f":{original_port.group(1)}", f":{allocated_port}")
        else:
            test_url = task.request  # No port in URL, use as-is
        
        # Run server in Docker
        def run_docker_target():
            cmd = utils.get_run_command()
            docker_cmd = utils.get_docker_command(cmd, allocated_port)
            process_manager.start_process(docker_cmd)
        
        thread = threading.Thread(target=run_docker_target)
        thread.start()
    else:
        # Native execution
        test_url = task.request
        
        def run_target():
            cmd = utils.get_run_command()
            process_manager.start_process(cmd, cwd=code_path)
        
        thread = threading.Thread(target=run_target)
        thread.start()
    
    try:
        # Wait for process to start
        if not process_manager.wait_for_start():
            return TaskResult(
                run=run,
                success=False,
                errors=[f"Failed to start {utils.language} process"],
                response=response,
                code=code,
                output="",
                expected_output=task.expected_output,
                tokens=(prompt_tokens, completion_tokens),
                mutated_code=mutated_code,
            )
        
        # Wait for server to be ready
        if not wait_for_server_ready(test_url):
            process_manager.terminate()
            return TaskResult(
                run=run,
                success=False,
                errors=["Server failed to start within timeout period"],
                response=response,
                code=code,
                output="",
                expected_output=task.expected_output,
                tokens=(prompt_tokens, completion_tokens),
                mutated_code=mutated_code,
            )
        
        # Make HTTP request
        try:
            http_response = requests.get(test_url, timeout=300)
            http_response.raise_for_status()
        except requests.RequestException as e:
            logging.error("Error during HTTP request: %s", e)
            return TaskResult(
                run=run,
                success=False,
                errors=["Failed to make HTTP request"],
                response=response,
                code=code,
                output="",
                expected_output=task.expected_output,
                tokens=(prompt_tokens, completion_tokens),
                mutated_code=mutated_code,
            )
        finally:
            process_manager.terminate()
        
        # Compare response to expected output
        if isinstance(task.expected_output, str):
            response_text = http_response.text
            return TaskResult(
                run=run,
                success=response_text.strip() == task.expected_output.strip(),
                errors=[],
                response=response,
                code=code,
                output=response_text,
                expected_output=task.expected_output,
                tokens=(prompt_tokens, completion_tokens),
                mutated_code=mutated_code,
            )
        elif isinstance(task.expected_output, dict):
            response_json = http_response.json()
            return TaskResult(
                run=run,
                success=are_json_values_equal(response_json, task.expected_output),
                errors=[],
                response=response,
                code=code,
                output=json.dumps(response_json),
                expected_output=task.expected_output,
                tokens=(prompt_tokens, completion_tokens),
                mutated_code=mutated_code,
            )
        else:
            return TaskResult(
                run=run,
                success=False,
                errors=["Invalid expected output type"],
                response=response,
                code=code,
                output="",
                expected_output=str(task.expected_output),
                tokens=(prompt_tokens, completion_tokens),
                mutated_code=mutated_code,
            )
    finally:
        # Release allocated port
        if allocated_port:
            port_manager.release_port(allocated_port)


def exec_call_common(task: TaskCall, model: str, run: int, utils: BaseLanguageUtils) -> TaskResult:
    """
    Common implementation for executing a TaskCall.
    """
    try:
        r = utils.query_code(task.prompt, model)
    except (ValueError, RuntimeError, TimeoutError) as e:
        return TaskResult.error(run, [str(e)])
    if not r:
        return TaskResult(
            run=run,
            success=False,
            errors=["Failed to query code"],
            response="",
            code="",
            output="",
            expected_output=task.expected_output,
            tokens=(0, 0),
            mutated_code="",
        )
    code, response, prompt_tokens, completion_tokens = r
    
    # Use the prepare_codebase_for_call method (which may be overridden)
    code_path = utils.prepare_codebase_for_call(code, task.input_contents)
    
    # Read the mutated code from the file
    mutated_code = utils.get_mutated_code(code_path) if code_path else ""
    
    if not code_path:
        return TaskResult(
            run=run,
            success=False,
            errors=["Failed to prepare codebase"],
            response=response,
            code=code,
            output="",
            expected_output=task.expected_output,
            tokens=(prompt_tokens, completion_tokens),
            mutated_code=mutated_code,
        )
    
    # Run validation
    result = utils.run_validation_wrapper(code_path)
    if not result.success:
        return TaskResult(
            run=run,
            success=False,
            errors=result.errors,
            response=response,
            code=code,
            output="",
            expected_output=task.expected_output,
            tokens=(prompt_tokens, completion_tokens),
            mutated_code=mutated_code,
        )
    
    # Build if needed
    result = utils.run_build_wrapper(code_path)
    if not result.success:
        return TaskResult(
            run=run,
            success=False,
            errors=result.errors,
            response=response,
            code=code,
            output="",
            expected_output=task.expected_output,
            tokens=(prompt_tokens, completion_tokens),
            mutated_code=mutated_code,
        )
    
    # Run the script
    result = utils.run_script_wrapper(code_path)
    if not result.success:
        return TaskResult(
            run=run,
            success=False,
            errors=result.errors,
            response=response,
            code=code,
            output="",
            expected_output=task.expected_output,
            tokens=(prompt_tokens, completion_tokens),
            mutated_code=mutated_code,
        )
    
    # Compare output
    actual_output = result.output.strip() if result.output else ""
    expected = task.expected_output
    
    if isinstance(expected, str):
        success = are_string_values_equal(actual_output, expected, task.lowercase)
    else:
        try:
            actual_json = json.loads(actual_output)
            success = are_json_values_equal(actual_json, expected)
        except json.JSONDecodeError:
            success = False
    
    return TaskResult(
        run=run,
        success=success,
        errors=[],
        response=response,
        code=code,
        output=actual_output,
        expected_output=expected,
        tokens=(prompt_tokens, completion_tokens),
        mutated_code=mutated_code,
    )


def exec_check_common(task: TaskCheck, model: str, run: int, utils: BaseLanguageUtils) -> TaskResult:
    """
    Common implementation for executing a TaskCheck.
    """
    try:
        r = utils.query_code(task.prompt, model)
    except (ValueError, RuntimeError, TimeoutError) as e:
        return TaskResult.error(run, [str(e)])
    if not r:
        return TaskResult(
            run=run,
            success=False,
            errors=["Failed to query code"],
            response="",
            code="",
            output="",
            expected_output="Code should validate successfully",
            tokens=(0, 0),
            mutated_code="",
        )
    code, response, prompt_tokens, completion_tokens = r
    
    code_path = utils.prepare_codebase(code)
    
    # Read the mutated code from the file
    mutated_code = utils.get_mutated_code(code_path) if code_path else ""
    
    if not code_path:
        return TaskResult(
            run=run,
            success=False,
            errors=["Failed to prepare codebase"],
            response=response,
            code=code,
            output="",
            expected_output="Code should validate successfully",
            tokens=(prompt_tokens, completion_tokens),
            mutated_code=mutated_code,
        )
    
    # Run validation
    result = utils.run_validation_wrapper(code_path)
    
    return TaskResult(
        run=run,
        success=result.success,
        errors=result.errors,
        response=response,
        code=code,
        output=result.output or "",
        expected_output="Code should validate successfully",
        tokens=(prompt_tokens, completion_tokens),
        mutated_code=mutated_code,
    )


def exec_contains_common(task: TaskContains, model: str, run: int, utils: BaseLanguageUtils) -> TaskResult:
    """
    Common implementation for executing a TaskContains.
    """
    from utils import check_contains_matches
    
    try:
        # For contains tasks, we directly request from the LLM without extracting code
        response, prompt_tokens, completion_tokens = request(
            task.prompt, model, utils.language
        )
    except (ValueError, RuntimeError, TimeoutError) as e:
        return TaskResult.error(run, [str(e)])
    
    if not response:
        return TaskResult(
            run=run,
            success=False,
            errors=["Failed to query code"],
            response="",
            code="",
            output="",
            expected_output="",
            tokens=(0, 0),
            mutated_code="",
        )
    
    # Check if response contains expected matches
    valid_position_found = check_contains_matches(response, task.matches, task.mode)
    
    return TaskResult(
        run=run,
        success=valid_position_found,
        errors=[] if valid_position_found else ["Contains check failed"],
        response=response,
        code="",
        output="",
        expected_output=json.dumps(
            {
                "matches": [
                    {
                        "contains": match.contains,
                        "before": match.before,
                        "after": match.after,
                    }
                    for match in task.matches
                ],
                "mode": task.mode,
            }
        ),
        tokens=(prompt_tokens, completion_tokens),
        mutated_code="",
    )