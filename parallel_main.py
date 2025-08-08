#!/usr/bin/env python3
"""
Parallel version of main.py using multiprocessing.Pool for faster execution.
This provides the same functionality but processes tasks in parallel.
"""

import os
import sys
import argparse
import logging
from decimal import getcontext
from typing import Optional, List

from task import Language
from db import ResultDB
from parallel_executor import parallel_execute


def setup_logging(verbose: bool = False):
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO

    # Configure root logger
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run LLM language benchmark tests in parallel"
    )

    # File/database options
    parser.add_argument(
        "filename", nargs="?", help="Results database filename (optional)"
    )

    # Model selection
    parser.add_argument(
        "--model", "--model_name", dest="model_name", help="Run only a specific model"
    )

    # Language selection
    parser.add_argument(
        "--language",
        choices=["swift", "rust", "typescript", "python", "php", "go", "lua", "kotlin"],
        help="Run only a specific language",
    )

    # Task selection
    parser.add_argument(
        "--task",
        "--task_number",
        dest="task_number",
        help='Run only a specific task (e.g., "simple.json")',
    )

    # Execution options
    parser.add_argument(
        "--skip-lang-specific",
        action="store_true",
        default=True,
        help="Skip language-specific tasks (default: True)",
    )

    parser.add_argument(
        "--include-lang-specific",
        action="store_true",
        help="Include language-specific tasks",
    )

    # Parallel execution options
    parser.add_argument(
        "--workers", type=int, default=8, help="Number of worker processes (default: 8)"
    )

    parser.add_argument(
        "--rate-limit",
        type=int,
        default=30,
        help="Maximum LLM API calls per minute (default: 30)",
    )

    # Other options
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be executed without running",
    )

    return parser.parse_args()


def get_models(specific_model: Optional[str] = None) -> List[str]:
    """Get list of models to test."""
    if specific_model:
        return [specific_model]

    return [
        "openrouter/mistralai/devstral-medium",
        "openrouter/google/gemini-2.5-pro",
        "openrouter/qwen/qwen3-30b-a3b-instruct-2507",
        "openrouter/z-ai/glm-4.5",
        "openrouter/z-ai/glm-4.5-air",
        "openrouter/qwen/qwen3-235b-a22b-thinking-2507",
        "openrouter/qwen/qwen3-coder",
        "openrouter/qwen/qwen3-235b-a22b-2507",
        "openrouter/moonshotai/kimi-k2",
        "openrouter/anthropic/claude-sonnet-4",
        # "openrouter/mistralai/devstral-small",
        "openrouter/qwen/qwen3-coder",
        "openrouter/google/gemini-2.5-flash-lite",
    ]

    # Default model list (same as main.py)
    return [
        "openrouter/qwen/qwen3-30b-a3b",
        "lmstudio/deepcogito_cogito-v1-preview-qwen-32b",
        "openrouter/openai/gpt-4.1-mini",
        "openrouter/openai/gpt-4.1",
        "openrouter/openai/gpt-4.1-nano",
        "openrouter/google/gemini-2.5-pro-preview-03-25",
        "openrouter/openai/o4-mini",
        "openrouter/google/gemini-2.0-flash-001",
        "openrouter/all-hands/openhands-lm-32b-v0.1",
        "openrouter/mistral/ministral-8b",
        "inception/mercury-coder-small",
        "togetherai/deepcogito/cogito-v1-preview-llama-70B",
        "togetherai/deepcogito/deepcogito/cogito-v1-preview-qwen-32B",
        "togetherai/deepcogito/cogito-v1-preview-qwen-14B",
        "openrouter/x-ai/grok-3-mini-beta",
        "openrouter/x-ai/grok-3-beta",
        "openrouter/nvidia/llama-3.1-nemotron-ultra-253b-v1:free",
        "openrouter/meta-llama/llama-4-maverick",
        "openrouter/meta-llama/llama-4-scout",
        "openrouter/quasar-alpha",
        "openrouter/qwen/qwen-2.5-coder-32b-instruct",
        "openrouter/qwen/qwen-2.5-72b-instruct",
        "openrouter/qwen/qwen-2.5-vl-72b-instruct",
        "openrouter/qwen/qwen2.5-vl-32b-instruct:free",
        "openrouter/cognitivecomputations/dolphin3.0-mistral-24b:free",
        "openrouter/google/gemini-2.5-pro-exp-03-25:free",
        "openrouter/qwen/qwen2.5-vl-32b-instruct:free",
        "openrouter/deepseek/deepseek-chat-v3-0324",
        "openrouter/featherless/qwerky-72b:free",
        "openrouter/mistralai/mistral-small-3.1-24b-instruct",
        "openrouter/open-r1/olympiccoder-7b:free",
        "openrouter/open-r1/olympiccoder-32b:free",
        "openrouter/steelskull/l3.3-electra-r1-70b",
        "openrouter/allenai/olmo-2-0325-32b-instruct",
        "openrouter/google/gemma-3-12b-it",
        "openrouter/cohere/command-a",
        "openrouter/rekaai/reka-flash-3:free",
        "openrouter/google/gemma-3-27b-it",
        "openrouter/thedrummer/anubis-pro-105b-v1",
        "openrouter/microsoft/phi-4-multimodal-instruct",
        "openrouter/qwen/qwq-32b",
        "openrouter/openai/o3-mini",
        "openrouter/qwen/qwen-turbo",
        "openrouter/qwen/qwen-plus",
        "openrouter/qwen/qwen-max",
        "openrouter/deepseek/deepseek-r1",
        "openrouter/deepseek/deepseek-chat",
        "openrouter/openai/o1-preview",
        "openrouter/deepseek/deepseek-r1-distill-llama-70b",
        "openrouter/mistralai/codestral-2501",
        "openrouter/microsoft/phi-4",
        "openrouter/meta-llama/llama-3.3-70b-instruct",
        "openrouter/amazon/nova-pro-v1",
        "openrouter/qwen/qwq-32b-preview",
        "openrouter/openai/gpt-4o-2024-11-20",
        "openrouter/mistralai/mistral-large-2411",
        "openrouter/anthropic/claude-3.5-haiku-20241022:beta",
        "openrouter/anthropic/claude-3.5-sonnet-20240620:beta",
        "openrouter/anthropic/claude-3.7-sonnet",
        "openrouter/openai/gpt-4o-mini",
        "openrouter/openai/gpt-4o",
        "openrouter/mistralai/mistral-small-24b-instruct-2501",
    ]


def get_languages(specific_language: Optional[str] = None) -> List[Language]:
    """Get list of languages to test."""
    if specific_language:
        return [Language(specific_language)]

    return [
        Language.SWIFT,
        Language.RUST,
        Language.TYPESCRIPT,
        Language.PYTHON,
        Language.PHP,
        Language.GO,
        Language.LUA,
        Language.KOTLIN,
    ]


def main():
    """Main entry point for parallel benchmark execution."""
    # Set decimal precision
    getcontext().prec = 16

    # Parse arguments
    args = parse_arguments()

    # Set up logging
    setup_logging(args.verbose)

    # Check for required environment variable
    if not os.environ.get("OPENROUTER_API_KEY"):
        logging.error("OPENROUTER_API_KEY environment variable must be set")
        sys.exit(1)

    # Initialize database
    db = ResultDB(filename=args.filename)

    # Get models and languages to test
    models = get_models(args.model_name)
    languages = get_languages(args.language)

    # Handle language-specific flag
    skip_lang_specific = (
        not args.include_lang_specific
        if args.include_lang_specific
        else args.skip_lang_specific
    )

    # Log configuration
    logging.info(f"Models to test: {len(models)}")
    logging.info(f"Languages to test: {[l.value for l in languages]}")
    logging.info(f"Worker processes: {args.workers} (max 1 per language)")
    logging.info(f"Rate limit: {args.rate_limit} calls/minute")
    logging.info(f"Skip language-specific: {skip_lang_specific}")
    if args.task_number:
        logging.info(f"Limited to task: {args.task_number}")

    # Dry run mode
    if args.dry_run:
        from parallel_executor import create_work_items
        from llm import model_info

        model_infos = model_info(models)
        work_items = create_work_items(
            models, languages, model_infos, skip_lang_specific, args.task_number, db
        )

        print(f"\nDry run - would process {len(work_items)} tasks:")
        print(f"- {len(models)} models")
        print(f"- {len(languages)} languages")
        print(
            f"- ~{len(work_items) // (len(models) * len(languages)) if models and languages else 0} tasks per model/language"
        )

        # Show first few tasks
        print("\nFirst 10 tasks:")
        for i, item in enumerate(work_items[:10]):
            print(
                f"  {i + 1}. {item.model} / {item.language.value} / {item.task.filename}"
            )

        if len(work_items) > 10:
            print(f"  ... and {len(work_items) - 10} more")

        return

    # Execute benchmark in parallel
    try:
        parallel_execute(
            models=models,
            languages=languages,
            db=db,
            skip_lang_specific=skip_lang_specific,
            limit=args.task_number,
            worker_processes=args.workers,
            llm_rate_limit=args.rate_limit,
        )
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Saving progress...")
        db.save_db()
        print("Progress saved.")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Fatal error: {e}", exc_info=True)
        db.save_db()
        sys.exit(1)


if __name__ == "__main__":
    main()
