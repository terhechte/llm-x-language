"""Kotlin Native language utilities for benchmark execution."""

import os
import shutil
import subprocess
import logging
from typing import List
from base_executor import BaseLanguageUtils
from utils import Result


class KotlinUtils(BaseLanguageUtils):
    """Kotlin Native specific language utilities."""

    def __init__(self):
        super().__init__(
            language="Kotlin", 
            template_name="kotlin_container", 
            main_file="src/nativeMain/kotlin/main.kt"
        )

    def get_language_aliases(self) -> List[str]:
        """Return common aliases for Kotlin."""
        return ["kotlin", "kt", "kotlinc-native"]

    def get_kotlin_binary(self) -> str:
        """Check which Kotlin binary aliases exist in PATH and return the first match."""
        for alias in self.get_language_aliases():
            if shutil.which(alias):
                return alias

        # If no alias is found, you might want to raise an exception or return a default
        raise FileNotFoundError("No Kotlin binary found in PATH")

    def validate_code(self, code: str) -> bool:
        """Basic validation to check if code is valid Kotlin."""
        # Check for basic Kotlin structure
        if not code.strip():
            return False
        
        # Very basic validation - check for common Kotlin keywords
        kotlin_indicators = ["fun ", "val ", "var ", "class ", "object ", "interface ", "enum "]
        has_kotlin = any(indicator in code for indicator in kotlin_indicators)
        
        # For single expressions, they might not have these keywords
        if not has_kotlin and len(code.strip().split('\n')) == 1:
            return True
            
        return has_kotlin

    def prepare_codebase_for_call(self, code: str, input_contents: str) -> str:
        """Prepare Kotlin code for TaskCall execution."""
        import time
        print(f"[DEBUG {time.time():.3f}] kotlin prepare_codebase_for_call: Received {len(code)} chars of code")
        print(f"[DEBUG {time.time():.3f}] kotlin prepare_codebase_for_call: Code preview: {code[:100]}...")
        
        # Check if code already has a main function
        if "fun main" in code:
            # If it has main, just use the code as-is
            print(f"[DEBUG {time.time():.3f}] kotlin prepare_codebase_for_call: Code already has main function")
            return self.prepare_codebase(code)
        
        # Validate that the code contains an example function
        if "fun example" not in code:
            # If no example function, the AI might have generated something else
            # Log this for debugging
            import logging
            logging.warning(f"Kotlin code does not contain 'fun example': {code[:200]}...")
            print(f"[DEBUG {time.time():.3f}] kotlin prepare_codebase_for_call: WARNING - No 'fun example' found!")
        
        # Escape the input contents for Kotlin string literal
        escaped_input = input_contents.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r')
        
        # Check if code already has imports
        has_imports = any(imp in code for imp in ["import ", "package "])
        
        if has_imports:
            # Code already has imports, just add main function
            wrapped_code = f"""{code.strip()}

fun main() {{
    val input = "{escaped_input}"
    val result = example(input)
    println(result)
}}
"""
        else:
            # Add full imports and main function
            wrapped_code = f"""import kotlin.text.*
import kotlinx.serialization.*
import kotlinx.serialization.json.*
import kotlinx.datetime.*
import io.ktor.client.*
import io.ktor.client.engine.cio.*
import io.ktor.client.request.*
import io.ktor.client.statement.*
import io.ktor.server.application.*
import io.ktor.server.engine.*
import io.ktor.server.cio.*
import io.ktor.server.response.*
import io.ktor.server.routing.*
import io.ktor.http.*

{code.strip()}

fun main() {{
    val input = "{escaped_input}"
    val result = example(input)
    println(result)
}}
"""
        print(f"[DEBUG {time.time():.3f}] kotlin prepare_codebase_for_call: Wrapped code length: {len(wrapped_code)}")
        result = self.prepare_codebase(wrapped_code)
        print(f"[DEBUG {time.time():.3f}] kotlin prepare_codebase_for_call: prepare_codebase returned: {result}")
        return result

    def prepare_codebase_for_contains(self, code: str) -> str:
        """Prepare Kotlin code for TaskContains execution."""
        # Ensure the code has a main function
        if "fun main" not in code:
            wrapped_code = f"""import kotlin.text.*
import kotlinx.serialization.*
import kotlinx.serialization.json.*
import kotlinx.datetime.*
import io.ktor.client.*
import io.ktor.client.engine.cio.*
import io.ktor.client.request.*
import io.ktor.client.statement.*
import io.ktor.server.application.*
import io.ktor.server.engine.*
import io.ktor.server.cio.*
import io.ktor.server.response.*
import io.ktor.server.routing.*
import io.ktor.http.*

{code.strip()}

fun main() {{
    // Entry point
}}
"""
            return self.prepare_codebase(wrapped_code)
        return self.prepare_codebase(code)

    def prepare_codebase_for_run(self, code: str) -> str:
        """Prepare Kotlin code for TaskRun execution (HTTP server)."""
        return self.prepare_codebase(code)

    def prepare_codebase_for_check(self, code: str, function_call: str) -> str:
        """Prepare Kotlin code for TaskCheck execution."""
        wrapped_code = f"""import kotlin.text.*
import kotlinx.serialization.*
import kotlinx.serialization.json.*
import kotlinx.datetime.*
import io.ktor.client.*
import io.ktor.client.engine.cio.*
import io.ktor.client.request.*
import io.ktor.client.statement.*
import io.ktor.server.application.*
import io.ktor.server.engine.*
import io.ktor.server.cio.*
import io.ktor.server.response.*
import io.ktor.server.routing.*
import io.ktor.http.*

{code.strip()}

fun main() {{
    {function_call}
}}
"""
        print(f"[DEBUG {time.time():.3f}] kotlin prepare_codebase_for_call: Wrapped code length: {len(wrapped_code)}")
        result = self.prepare_codebase(wrapped_code)
        print(f"[DEBUG {time.time():.3f}] kotlin prepare_codebase_for_call: prepare_codebase returned: {result}")
        return result

    def run_validation(self, code_path: str) -> Result:
        """Build Kotlin Native project using Gradle."""
        import time
        try:
            print(f"[DEBUG {time.time():.3f}] kotlin run_validation: Starting validation for {code_path}")
            
            # Check if the main.kt file exists before build
            main_file_path = os.path.join(code_path, self.main_file)
            if os.path.exists(main_file_path):
                file_size = os.path.getsize(main_file_path)
                print(f"[DEBUG {time.time():.3f}] kotlin run_validation: main.kt exists, size: {file_size} bytes")
                # Read first 200 chars to verify content
                with open(main_file_path, 'r') as f:
                    content_preview = f.read(200)
                    print(f"[DEBUG {time.time():.3f}] kotlin run_validation: File preview: {content_preview}...")
            else:
                print(f"[DEBUG {time.time():.3f}] kotlin run_validation: WARNING - main.kt does not exist!")
            
            # Determine OS-specific gradlew command
            gradlew_cmd = "./gradlew" if os.name != 'nt' else "gradlew.bat"
            
            # Skip clean to avoid potential issues with file timing
            # Previous builds will be overwritten anyway
            
            # Build the native executable
            print(f"[DEBUG {time.time():.3f}] kotlin run_validation: Running gradle command: {gradlew_cmd} nativeBinaries")
            result = subprocess.run(
                [gradlew_cmd, "nativeBinaries", "--console=plain"],
                cwd=code_path,
                capture_output=True,
                text=True,
                timeout=120,  # Increased timeout for first build
                shell=(os.name == 'nt')  # Use shell on Windows
            )

            print(f"[DEBUG {time.time():.3f}] kotlin run_validation: Gradle completed with return code: {result.returncode}")
            
            # Check file status after build
            if os.path.exists(main_file_path):
                file_size = os.path.getsize(main_file_path)
                print(f"[DEBUG {time.time():.3f}] kotlin run_validation: After build - main.kt exists, size: {file_size} bytes")
            else:
                print(f"[DEBUG {time.time():.3f}] kotlin run_validation: After build - WARNING - main.kt missing!")
            
            if result.returncode != 0:
                print(f"[DEBUG {time.time():.3f}] kotlin run_validation: Build failed")
                print(f"[DEBUG {time.time():.3f}] kotlin run_validation: stderr: {result.stderr[:500]}...")
                errors = [result.stderr] if result.stderr else ["Compilation failed"]
                return Result(success=False, errors=errors)

            print(f"[DEBUG {time.time():.3f}] kotlin run_validation: Build succeeded")
            return Result(success=True, errors=[])
        except subprocess.SubprocessError as e:
            logging.error("Error during Kotlin compilation: %s", e)
            return Result(success=False, errors=[str(e)])

    def get_run_command(self) -> List[str]:
        """Get the command to run the compiled Kotlin Native executable."""
        # The executable is located in build/bin/native/releaseExecutable/ with .kexe extension
        return ["./build/bin/native/releaseExecutable/main.kexe"]


# Create singleton instance
kotlin_utils = KotlinUtils()
