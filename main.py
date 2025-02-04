import os
import logging
import sys
from task import load_all_tasks, Language
from executor import Executor
from db import ResultDB
from llm import model_info, ModelInfo
from decimal import Decimal, getcontext
import time


def setup_logging():
    # Create a handler that writes log messages to sys.stdout
    handler = logging.StreamHandler(sys.stdout)

    # Define a simple format for log messages
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)

    # Get the root logger (or any named logger you prefer)
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # Set the threshold to debug
    logger.addHandler(handler)


def execute_all_tasks(
    model: str,
    language: Language,
    db: ResultDB,
    run: int,
    limit: str | None,
    skip_lang_specific: bool,
    info: ModelInfo,
) -> Decimal:
    """
    Loads and executes all tasks, calling the appropriate executor based on task type.
    Returns a dictionary with task results.
    """
    tasks = load_all_tasks(language, skip_lang_specific)
    executor = Executor(language)
    total_cost = Decimal(0)
    for task in tasks:
        if limit and task.filename != limit:
            continue

        if db.has_result(run, task.filename, model, language.value):
            print(f"Skipping task: {task.filename} because it already exists")
            continue

        print(f"Executing task: {task.filename}")
        current_time = time.time()
        result = executor.call(task, model, run)
        duration = time.time() - current_time

        # calculate the costs
        pricing = Decimal(info.prompt_pricing)
        completion = Decimal(info.completion_pricing)
        prompt_tokens = Decimal(result.tokens[0])
        completion_tokens = Decimal(result.tokens[1])
        cost = pricing * prompt_tokens + completion * completion_tokens
        total_cost += cost

        # Store result in database
        db.add_result(
            result=result.result,
            model=model,
            task_name=task.filename,
            prompt=task.prompt,
            code=result.code,
            run=run,
            task_type=task.__class__.__name__,
            response=result.response,
            output=result.output,
            expected_output=result.expected_output,
            language=language,
            errors=result.errors,
            cost=cost,
            duration=duration,
            is_lang_specific=task.is_lang_specific,
        )
    return total_cost


def main():
    getcontext().prec = 16
    if not os.environ.get("OPENROUTER_API_KEY"):
        raise ValueError("OPENROUTER_API_KEY environment variable must be set")

    # Add optional argument parsing
    filename = None
    if len(sys.argv) > 1:
        filename = sys.argv[1]

    db = ResultDB(filename=filename)
    setup_logging()
    multi_runs = True
    languages = [Language.SWIFT, Language.RUST, Language.TYPESCRIPT, Language.PYTHON]
    limit = None  # "types1.json"
    skip_lang_specific = False  # should the lang specific tasks be skipped
    models = [
        "openai/o3-mini",
        "qwen/qwen-turbo",
        "qwen/qwen-plus",
        "qwen/qwen-max",
        "deepseek/deepseek-r1",
        "deepseek/deepseek-chat",
        "openai/o1-preview",
        "deepseek/deepseek-r1-distill-llama-70b",
        "mistralai/codestral-2501",
        "microsoft/phi-4",
        "meta-llama/llama-3.3-70b-instruct",
        "amazon/nova-pro-v1",
        "qwen/qwq-32b-preview",
        "openai/gpt-4o-2024-11-20",
        "mistralai/mistral-large-2411",
        "anthropic/claude-3.5-haiku-20241022:beta",
        "anthropic/claude-3.5-sonnet:beta",
        "openai/gpt-4o-mini",
        "mistralai/mistral-small-24b-instruct-2501",
    ]
    model_infos = model_info(models)
    for model in models:
        for language in languages:
            info = model_infos[model]
            cost = Decimal(0)
            current_time = time.time()
            if multi_runs:
                for n in range(1, 4):
                    total_cost = execute_all_tasks(
                        model,
                        language,
                        db,
                        n,
                        limit=limit,
                        skip_lang_specific=skip_lang_specific,
                        info=info,
                    )
                    cost += total_cost
            else:
                total_cost = execute_all_tasks(
                    model,
                    language,
                    db,
                    1,
                    limit=limit,
                    skip_lang_specific=skip_lang_specific,
                    info=info,
                )
                cost += total_cost
            db.set_total_costs(model, language.value, cost)
            db.set_total_duration(model, language.value, time.time() - current_time)
        print(f"Time taken: {time.time() - current_time}")
        db.save_db()
        print(db.analyze())


if __name__ == "__main__":
    main()
