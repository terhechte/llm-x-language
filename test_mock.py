"""Test script to verify code generation using mock provider."""

import os
import shutil
from pathlib import Path
from task import TaskCall, TaskCheck, TaskRun, Language
from executor import Executor
from utils import TaskResult
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_test_tasks():
    """Create simple test tasks for each task type."""
    tasks = {
        "check": TaskCheck(
            filename="test_check",
            prompt="Write a function called example that takes a string input and returns it"
        ),
        "call": TaskCall(
            filename="test_call",
            prompt="Write a function called example that takes a string input and returns it",
            input_contents="test_output",
            expected_output="test_output"
        ),
        "run": TaskRun(
            filename="test_run",
            prompt="Write an HTTP server that responds with 'Hello' on GET /",
            request="/",
            expected_output="Hello"
        )
    }
    return tasks


def save_generated_code(language: Language, task_type: str, output_dir: Path):
    """Copy the generated code to the output directory for inspection."""
    # Map language to file extension
    extensions = {
        Language.PYTHON: ".py",
        Language.RUST: ".rs",
        Language.TYPESCRIPT: ".ts",
        Language.SWIFT: ".swift",
        Language.KOTLIN: ".kt",
        Language.GO: ".go",
        Language.PHP: ".php",
        Language.LUA: ".lua"
    }
    
    # Map language to container name
    container_names = {
        Language.PYTHON: "python_container",
        Language.RUST: "rust_container",
        Language.TYPESCRIPT: "typescript_container",
        Language.SWIFT: "swift_container",
        Language.KOTLIN: "kotlin_container",
        Language.GO: "go_container",
        Language.PHP: "php_container",
        Language.LUA: "lua_container"
    }
    
    # Find the main file based on language
    main_files = {
        Language.PYTHON: "main.py",
        Language.RUST: "src/main.rs",
        Language.TYPESCRIPT: "src/index.ts",
        Language.SWIFT: "Sources/main.swift",
        Language.KOTLIN: "src/nativeMain/kotlin/main.kt",
        Language.GO: "main.go",
        Language.PHP: "main.php",
        Language.LUA: "main.lua"
    }
    
    # Construct the path to the dojo container
    dojo_path = Path(__file__).parent / "dojo" / container_names.get(language, "python_container")
    src_file = dojo_path / main_files.get(language, "main.py")
    
    if src_file.exists():
        dst_file = output_dir / f"{language.value}_{task_type}{extensions.get(language, '.txt')}"
        shutil.copy2(src_file, dst_file)
        logger.info(f"Saved {language.value} {task_type} code to {dst_file}")
        
        # Also print the content for immediate inspection
        with open(dst_file, 'r') as f:
            content = f.read()
            print(f"\n--- {language.value} {task_type} ---")
            print(content)
            print("---\n")
    else:
        logger.warning(f"Could not find source file: {src_file}")


def run_test_for_language(language: Language, output_dir: Path):
    """Run all test tasks for a given language."""
    logger.info(f"Testing {language.value}...")
    executor = Executor(language)
    tasks = create_test_tasks()
    
    for task_type, task in tasks.items():
        # Skip run tasks for now as they're more complex
        if task_type == "run":
            logger.info(f"Skipping {task_type} task for {language.value}")
            continue
            
        logger.info(f"Running {task_type} task for {language.value}")
        
        try:
            # Use mock model
            result: TaskResult = executor.call(task, "mock/test", run=1)
            
            # Save the generated code from the dojo directory
            save_generated_code(language, task_type, output_dir)
            
            logger.info(f"Result for {language.value} {task_type}: success={result.result.success}")
            if result.errors:
                logger.error(f"Errors: {result.errors}")
                
        except Exception as e:
            logger.error(f"Failed to run {task_type} for {language.value}: {e}")


def main():
    """Main test function."""
    # Create output directory
    output_dir = Path("mock-test")
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir()
    
    # Test all languages
    languages = [
        Language.PYTHON,
        Language.RUST,
        Language.TYPESCRIPT,
        Language.SWIFT,
        Language.KOTLIN,
        Language.GO,
        Language.PHP,
        Language.LUA
    ]
    
    for language in languages:
        run_test_for_language(language, output_dir)
    
    logger.info(f"\nTest complete! Check the '{output_dir}' directory for generated code.")


if __name__ == "__main__":
    main()