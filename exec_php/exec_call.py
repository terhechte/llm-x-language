import json
import logging
from task import TaskCall
from utils import are_json_values_equal, are_string_values_equal, TaskResult
from exec_php.php_utils import prepare_codebase, query_code, run_php_check, run_php_script


def exec_call(task: TaskCall, model: str, run: int) -> TaskResult:
    """
    Execute PHP code and compare output with expected result
    """
    try:
        r = query_code(task.prompt, model)
    except (ValueError, RuntimeError, TimeoutError) as e:
        return TaskResult.error(run, [str(e)])
    logging.debug("Python code: %s", r)
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
    php_code, response, prompt_tokens, completion_tokens = r

    php_code = php_code.strip()
    if php_code.endswith("?>"):
        php_code = php_code[:-2]
    if not php_code.startswith("<?php") and not php_code.startswith("<?"):
        php_code = "<?php\n" + php_code

    # Wrap the code to handle input
    php_code = f"""
{php_code.strip()}

$str = <<<TEXT
{task.input_contents}
TEXT;

echo example($str);
"""

    # Prepare the codebase
    code_path = prepare_codebase(php_code)
    if not code_path:
        logging.error("Failed to prepare codebase")
        return TaskResult(
            run=run,
            success=False,
            errors=["Failed to prepare codebase"],
            response=response,
            code=php_code,
            output="",
            expected_output=task.expected_output,
            tokens=(prompt_tokens, completion_tokens),
        )

    # Run PHP syntax check
    result = run_php_check(code_path)
    if not result.success:
        logging.error("Failed PHP syntax check")
        return TaskResult(
            run=run,
            success=False,
            errors=["Failed PHP syntax check"] + result.errors,
            response=response,
            code=php_code,
            output="",
            expected_output=task.expected_output,
            tokens=(prompt_tokens, completion_tokens),
        )

    # Execute the PHP script
    output = run_php_script(code_path)
    logging.debug("Output: %s", output)
    if not output.success:
        return TaskResult(
            run=run,
            success=False,
            errors=["Failed to run PHP script"] + output.errors,
            response=response,
            code=php_code,
            output="",
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
            code=php_code,
            output=output.errors[0],
            expected_output=task.expected_output,
            tokens=(prompt_tokens, completion_tokens),
        )
    elif isinstance(task.expected_output, (dict, list)):
        try:
            output_json = json.loads(output.errors[0])
            return TaskResult(
                run=run,
                success=are_json_values_equal(output_json, task.expected_output),
                errors=[],
                response=response,
                code=php_code,
                output=json.dumps(output_json),
                expected_output=json.dumps(task.expected_output),
                tokens=(prompt_tokens, completion_tokens),
            )
        except json.JSONDecodeError:
            return TaskResult(
                run=run,
                success=False,
                errors=["Output is not valid JSON"],
                response=response,
                code=php_code,
                output=output.errors[0],
                expected_output=json.dumps(task.expected_output),
                tokens=(prompt_tokens, completion_tokens),
            )
    else:
        return TaskResult(
            run=run,
            success=False,
            errors=["Unsupported expected output type"],
            response=response,
            code=php_code,
            output=output.errors[0],
            expected_output=str(task.expected_output),
            tokens=(prompt_tokens, completion_tokens),
        )