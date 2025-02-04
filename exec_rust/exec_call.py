import logging
import json
from task import TaskCall
from utils import are_string_values_equal, are_json_values_equal, TaskResult
from exec_rust.rust_utils import (
    query_code,
    prepare_codebase,
    run_cargo_check,
    run_rust_project_with_output,
    remove_rust_main_function,
)


def exec_call(task: TaskCall, model: str, run: int) -> TaskResult:
    """
    Execute a TaskCall for Rust code.
    Returns a TaskResult containing the execution results and relevant code/output.
    """
    try:
        r = query_code(task.prompt, model)
    except (ValueError, RuntimeError, TimeoutError) as e:
        return TaskResult.error(run, [str(e)])
    logging.debug("Rust code: %s", r)
    if not r:
        return TaskResult(
            run=run,
            success=False,
            errors=["Failed to query code"],
            response="",
            code="",
            output="",
            expected_output="",
            tokens=(0, 0),
        )
    rust_code, response, prompt_tokens, completion_tokens = r

    rust_code = remove_rust_main_function(rust_code)

    # add the fn main to the codebase
    should_unwrap = ""
    for line in rust_code.split("\n"):
        if line.strip().find("fn example") != -1:
            if line.find("Result<") != -1:
                should_unwrap = ".unwrap()"
                break

    if rust_code.find("async fn example") == -1:
        rust_code += f"""
fn main() {{
    println!("{{}}", example(r#"{task.input_contents}"#.to_string()){should_unwrap});
}}

"""
    else:
        rust_code += f"""
#[tokio::main]
async fn main() {{
    println!("{{}}", example(r#"{task.input_contents}"#.to_string()).await{should_unwrap});
}}

"""

    code_path = prepare_codebase(rust_code)
    if not code_path:
        logging.error("Failed to prepare codebase")
        return TaskResult(
            run=run,
            success=False,
            errors=["Failed to prepare codebase"],
            response=response,
            code=rust_code,
            output="",
            expected_output=task.expected_output,
            tokens=(prompt_tokens, completion_tokens),
        )

    # Run cargo check
    result = run_cargo_check(code_path)
    if not result.success:
        logging.error("Failed to run cargo check")
        return TaskResult(
            run=run,
            success=False,
            errors=["Failed to run cargo check"] + result.errors,
            response=response,
            code=rust_code,
            output="",
            expected_output=task.expected_output,
            tokens=(prompt_tokens, completion_tokens),
        )

    output = run_rust_project_with_output(code_path)
    logging.debug("Output: %s", output)
    if not output.success:
        return TaskResult(
            run=run,
            success=False,
            errors=["Failed to run rust project"] + output.errors,
            response=response,
            code=rust_code,
            output=output.errors[0],
            expected_output=task.expected_output,
            tokens=(prompt_tokens, completion_tokens),
        )

    if isinstance(task.expected_output, str):
        return TaskResult(
            run=run,
            success=are_string_values_equal(
                output.errors[0], task.expected_output, task.lowercase
            ),
            errors=[],
            response=response,
            code=rust_code,
            output=output.errors[0],
            expected_output=task.expected_output,
            tokens=(prompt_tokens, completion_tokens),
        )
    elif isinstance(task.expected_output, dict) or isinstance(
        task.expected_output, list
    ):
        try:
            output_json = json.loads(output.errors[0])
            return TaskResult(
                run=run,
                success=are_json_values_equal(output_json, task.expected_output),
                errors=[],
                response=response,
                code=rust_code,
                output=json.dumps(output_json),
                expected_output=json.dumps(task.expected_output),
                tokens=(prompt_tokens, completion_tokens),
            )
        except json.JSONDecodeError:
            logging.error("Output string is not valid JSON")
            logging.debug("Output: %s", output)
            return TaskResult(
                run=run,
                success=False,
                errors=["Output string is not valid JSON"],
                response=response,
                code=rust_code,
                output=output.errors[0] if output.errors else "",
                expected_output=json.dumps(task.expected_output),
                tokens=(prompt_tokens, completion_tokens),
            )
    else:
        return TaskResult(
            run=run,
            success=False,
            errors=["Invalid expected output type"],
            response=response,
            code=rust_code,
            output=output.errors[0] if output.errors else "",
            expected_output=str(task.expected_output),
            tokens=(prompt_tokens, completion_tokens),
        )
