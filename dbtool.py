#!/usr/bin/env python3
"""
Database tool for managing benchmark results.
Provides utilities to filter, remove, and merge result databases.
"""

import argparse
import json
from pathlib import Path
from typing import List, Optional
from db import ResultDB, TestResult
from decimal import Decimal


class DBTool:
    def __init__(self, db_path: str):
        """Initialize DBTool with a database file path."""
        self.db = ResultDB(db_path)
        self.db_path = db_path
        print(f"Loaded database: {db_path}")
        print(f"Total results: {len(self.db.results)}")
    
    def remove_model(self, model_name: str) -> int:
        """Remove all results for a specific model/LLM.
        
        Args:
            model_name: Name of the model to remove
            
        Returns:
            Number of results removed
        """
        original_count = len(self.db.results)
        self.db.results = [r for r in self.db.results if r.model != model_name]
        
        # Also remove from costs and durations
        if model_name in self.db.costs:
            del self.db.costs[model_name]
        if model_name in self.db.durations:
            del self.db.durations[model_name]
        
        removed = original_count - len(self.db.results)
        if removed > 0:
            self.db.save_db()
            print(f"Removed {removed} results for model '{model_name}'")
        else:
            print(f"No results found for model '{model_name}'")
        return removed
    
    def remove_language(self, language: str) -> int:
        """Remove all results for a specific language.
        
        Args:
            language: Language to remove (python, rust, typescript, etc.)
            
        Returns:
            Number of results removed
        """
        original_count = len(self.db.results)
        self.db.results = [r for r in self.db.results if r.language.lower() != language.lower()]
        
        # Update costs and durations
        for model in list(self.db.costs.keys()):
            if language in self.db.costs[model]:
                del self.db.costs[model][language]
            if not self.db.costs[model]:  # Remove model if no languages left
                del self.db.costs[model]
        
        for model in list(self.db.durations.keys()):
            if language in self.db.durations[model]:
                del self.db.durations[model][language]
            if not self.db.durations[model]:  # Remove model if no languages left
                del self.db.durations[model]
        
        removed = original_count - len(self.db.results)
        if removed > 0:
            self.db.save_db()
            print(f"Removed {removed} results for language '{language}'")
        else:
            print(f"No results found for language '{language}'")
        return removed
    
    def remove_task(self, task_name: str) -> int:
        """Remove all results for a specific task (all runs).
        
        Args:
            task_name: Name of the task to remove
            
        Returns:
            Number of results removed
        """
        original_count = len(self.db.results)
        self.db.results = [r for r in self.db.results if r.task_name != task_name]
        
        removed = original_count - len(self.db.results)
        if removed > 0:
            self.db.save_db()
            print(f"Removed {removed} results for task '{task_name}'")
        else:
            print(f"No results found for task '{task_name}'")
        return removed
    
    def remove_language_task_type(self, language: str, task_type: str) -> int:
        """Remove all results for a specific language and task type combination.
        
        Args:
            language: Language to filter (python, rust, typescript, etc.)
            task_type: Task type to filter (call, check, contains, run)
            
        Returns:
            Number of results removed
        """
        original_count = len(self.db.results)
        self.db.results = [
            r for r in self.db.results 
            if not (r.language.lower() == language.lower() and r.task_type.lower() == task_type.lower())
        ]
        
        removed = original_count - len(self.db.results)
        if removed > 0:
            self.db.save_db()
            print(f"Removed {removed} results for language '{language}' with task type '{task_type}'")
        else:
            print(f"No results found for language '{language}' with task type '{task_type}'")
        return removed
    
    def list_models(self) -> List[str]:
        """List all unique models in the database."""
        models = set(r.model for r in self.db.results)
        return sorted(list(models))
    
    def list_languages(self) -> List[str]:
        """List all unique languages in the database."""
        languages = set(r.language for r in self.db.results)
        return sorted(list(languages))
    
    def list_tasks(self) -> List[str]:
        """List all unique task names in the database."""
        tasks = set(r.task_name for r in self.db.results)
        return sorted(list(tasks))
    
    def list_task_types(self) -> List[str]:
        """List all unique task types in the database."""
        task_types = set(r.task_type for r in self.db.results)
        return sorted(list(task_types))
    
    def stats(self):
        """Print statistics about the database."""
        print("\n=== Database Statistics ===")
        print(f"Total results: {len(self.db.results)}")
        print(f"Models: {len(self.list_models())}")
        print(f"Languages: {len(self.list_languages())}")
        print(f"Tasks: {len(self.list_tasks())}")
        print(f"Task Types: {len(self.list_task_types())}")
        
        # Success rate
        if self.db.results:
            success_count = sum(1 for r in self.db.results if r.success)
            success_rate = (success_count / len(self.db.results)) * 100
            print(f"Overall success rate: {success_rate:.2f}%")
        
        # List all models
        models = self.list_models()
        if models:
            print(f"\n=== Models in Database ({len(models)}) ===")
            for model in models:
                # Count results for this model
                model_count = sum(1 for r in self.db.results if r.model == model)
                model_success = sum(1 for r in self.db.results if r.model == model and r.success)
                model_rate = (model_success / model_count * 100) if model_count > 0 else 0
                print(f"  - {model:<40} ({model_count:>4} results, {model_rate:>5.1f}% success)")
    
    def show_task_response_lengths(self, model_filter: Optional[str] = None):
        """Show all unique task names with their average response lengths.
        
        Args:
            model_filter: Optional model name to filter results
        """
        from collections import defaultdict
        
        # Filter results by model if specified
        results_to_analyze = self.db.results
        if model_filter:
            results_to_analyze = [r for r in self.db.results if r.model == model_filter]
            if not results_to_analyze:
                print(f"No results found for model '{model_filter}'")
                return
            print(f"Filtering results for model: {model_filter}")
        
        # Collect response lengths for each task
        task_response_data = defaultdict(list)
        
        for result in results_to_analyze:
            task_name = Path(result.task_name).name  # Extract just the filename
            response_length = len(result.response) if result.response else 0
            task_response_data[task_name].append(response_length)
        
        if not task_response_data:
            print("No tasks found in the database")
            return
        
        # Calculate statistics for each task
        task_stats = []
        for task_name, lengths in task_response_data.items():
            avg_length = sum(lengths) / len(lengths)
            min_length = min(lengths)
            max_length = max(lengths)
            count = len(lengths)
            
            task_stats.append({
                'task': task_name,
                'avg_length': avg_length,
                'min_length': min_length,
                'max_length': max_length,
                'count': count
            })
        
        # Sort by task name
        task_stats.sort(key=lambda x: x['task'])
        
        # Print table header
        print("\n=== Task Response Lengths ===")
        print(f"{'Task Name':<30} | {'Avg Length':>12} | {'Min':>8} | {'Max':>8} | {'Count':>6}")
        print("-" * 75)
        
        # Print each task's stats
        for stats in task_stats:
            print(f"{stats['task']:<30} | {stats['avg_length']:>12.0f} | "
                  f"{stats['min_length']:>8} | {stats['max_length']:>8} | {stats['count']:>6}")
        
        # Print summary
        print("-" * 75)
        total_responses = sum(stats['count'] for stats in task_stats)
        overall_avg = sum(stats['avg_length'] * stats['count'] for stats in task_stats) / total_responses if total_responses > 0 else 0
        print(f"{'TOTAL':<30} | {overall_avg:>12.0f} | {'':>8} | {'':>8} | {total_responses:>6}")
        print(f"\nTotal unique tasks: {len(task_stats)}")


def merge_databases(
    input_files: List[str], 
    output_file: str, 
    priority: str = "first"
) -> None:
    """Merge multiple databases into a new database.
    
    Args:
        input_files: List of database file paths to merge
        output_file: Path for the merged output database
        priority: Which database takes priority for duplicates ("first" or "last")
    """
    if not input_files:
        raise ValueError("No input files provided")
    
    # Create output database
    merged_db = ResultDB(output_file)
    merged_db.results = []  # Start with empty results
    merged_db.costs = {}
    merged_db.durations = {}
    
    seen_results = set()
    
    # Process files based on priority
    files_to_process = input_files if priority == "first" else reversed(input_files)
    
    for file_path in files_to_process:
        print(f"Processing: {file_path}")
        source_db = ResultDB(file_path)
        
        for result in source_db.results:
            # Create unique key for result
            result_key = (result.run, result.task_name, result.model, result.language)
            
            if result_key not in seen_results:
                merged_db.results.append(result)
                seen_results.add(result_key)
        
        # Merge costs (take max or sum based on use case)
        for model, costs in source_db.costs.items():
            if model not in merged_db.costs:
                merged_db.costs[model] = {}
            for lang, cost in costs.items():
                if lang not in merged_db.costs[model]:
                    merged_db.costs[model][lang] = cost
                elif priority == "last":
                    merged_db.costs[model][lang] = cost
        
        # Merge durations
        for model, durations in source_db.durations.items():
            if model not in merged_db.durations:
                merged_db.durations[model] = {}
            for lang, duration in durations.items():
                if lang not in merged_db.durations[model]:
                    merged_db.durations[model][lang] = duration
                elif priority == "last":
                    merged_db.durations[model][lang] = duration
    
    merged_db.save_db()
    print(f"\nMerged {len(input_files)} databases into {output_file}")
    print(f"Total results in merged database: {len(merged_db.results)}")


def main():
    parser = argparse.ArgumentParser(description="Database tool for managing benchmark results")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Remove model command
    remove_model_parser = subparsers.add_parser("remove-model", help="Remove all results for a specific model")
    remove_model_parser.add_argument("db", help="Database file path")
    remove_model_parser.add_argument("model", help="Model name to remove")
    
    # Remove language command
    remove_lang_parser = subparsers.add_parser("remove-language", help="Remove all results for a specific language")
    remove_lang_parser.add_argument("db", help="Database file path")
    remove_lang_parser.add_argument("language", help="Language to remove")
    
    # Remove task command
    remove_task_parser = subparsers.add_parser("remove-task", help="Remove all results for a specific task")
    remove_task_parser.add_argument("db", help="Database file path")
    remove_task_parser.add_argument("task", help="Task name to remove")
    
    # Remove language+task_type command
    remove_lang_type_parser = subparsers.add_parser(
        "remove-lang-type", 
        help="Remove all results for a language and task type"
    )
    remove_lang_type_parser.add_argument("db", help="Database file path")
    remove_lang_type_parser.add_argument("language", help="Language to filter")
    remove_lang_type_parser.add_argument("task_type", help="Task type (call, check, contains, run)")
    
    # Merge command
    merge_parser = subparsers.add_parser("merge", help="Merge multiple databases")
    merge_parser.add_argument("-o", "--output", required=True, help="Output database file path")
    merge_parser.add_argument(
        "-p", "--priority", 
        choices=["first", "last"], 
        default="first",
        help="Which database takes priority for duplicates (default: first)"
    )
    merge_parser.add_argument("inputs", nargs="+", help="Input database files to merge")
    
    # List commands
    list_parser = subparsers.add_parser("list", help="List items in database")
    list_parser.add_argument("db", help="Database file path")
    list_parser.add_argument(
        "type", 
        choices=["models", "languages", "tasks", "task-types"],
        help="What to list"
    )
    
    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show database statistics")
    stats_parser.add_argument("db", help="Database file path")
    
    # Tasks command - show task names and response lengths
    tasks_parser = subparsers.add_parser("tasks", help="Show task names and response length statistics")
    tasks_parser.add_argument("db", help="Database file path")
    tasks_parser.add_argument("-m", "--model", help="Filter results by specific model", default=None)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Execute commands
    if args.command == "remove-model":
        tool = DBTool(args.db)
        tool.remove_model(args.model)
    
    elif args.command == "remove-language":
        tool = DBTool(args.db)
        tool.remove_language(args.language)
    
    elif args.command == "remove-task":
        tool = DBTool(args.db)
        tool.remove_task(args.task)
    
    elif args.command == "remove-lang-type":
        tool = DBTool(args.db)
        tool.remove_language_task_type(args.language, args.task_type)
    
    elif args.command == "merge":
        merge_databases(args.inputs, args.output, args.priority)
    
    elif args.command == "list":
        tool = DBTool(args.db)
        if args.type == "models":
            items = tool.list_models()
            print(f"\n=== Models ({len(items)}) ===")
            for item in items:
                print(f"  - {item}")
        elif args.type == "languages":
            items = tool.list_languages()
            print(f"\n=== Languages ({len(items)}) ===")
            for item in items:
                print(f"  - {item}")
        elif args.type == "tasks":
            items = tool.list_tasks()
            print(f"\n=== Tasks ({len(items)}) ===")
            for item in items:
                print(f"  - {item}")
        elif args.type == "task-types":
            items = tool.list_task_types()
            print(f"\n=== Task Types ({len(items)}) ===")
            for item in items:
                print(f"  - {item}")
    
    elif args.command == "stats":
        tool = DBTool(args.db)
        tool.stats()
    
    elif args.command == "tasks":
        tool = DBTool(args.db)
        tool.show_task_response_lengths(model_filter=args.model)


if __name__ == "__main__":
    main()