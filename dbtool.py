#!/usr/bin/env python3
"""
Database tool for managing benchmark results.
Provides utilities to filter, remove, and merge result databases.
"""

import argparse
import json
import re
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
    
    def remove_by_error_pattern(self, language: str, error_pattern: str, confirm: bool = True, flag_only: bool = False) -> int:
        """Remove or flag all results for a specific language where errors match a regex pattern.
        
        Args:
            language: Language to filter (python, rust, typescript, etc.) or "all" for all languages
            error_pattern: Regular expression pattern to match in errors
            confirm: Whether to ask for confirmation before deletion/flagging
            flag_only: If True, flag entries with retry=True instead of removing them
            
        Returns:
            Number of results removed or flagged
        """
        import sys
        
        # Compile the regex pattern
        try:
            pattern = re.compile(error_pattern, re.IGNORECASE | re.MULTILINE)
        except re.error as e:
            print(f"Invalid regex pattern: {e}")
            return 0
        
        # Find matching results
        matching_results = []
        language_counts = {}  # Track matches per language
        model_counts = {}  # Track matches per model
        
        for result in self.db.results:
            # Check if language matches (or if we're searching all)
            if language.lower() != "all" and result.language.lower() != language.lower():
                continue
            
            # Check if any error matches the pattern
            if result.errors:
                for error in result.errors:
                    if pattern.search(error):
                        matching_results.append(result)
                        # Track language for statistics
                        lang = result.language
                        language_counts[lang] = language_counts.get(lang, 0) + 1
                        # Track model for statistics
                        model = result.model
                        model_counts[model] = model_counts.get(model, 0) + 1
                        break
        
        # Show statistics
        action = "Flag" if flag_only else "Remove"
        print(f"\n=== {action} by Error Pattern ===")
        print(f"Pattern: {error_pattern}")
        
        if language.lower() == "all":
            print(f"Language: ALL")
            print(f"Total entries in database: {len(self.db.results)}")
            print(f"Total entries matching pattern: {len(matching_results)}")
            
            if language_counts:
                print(f"\nBreakdown by language:")
                for lang, count in sorted(language_counts.items()):
                    total_lang = sum(1 for r in self.db.results if r.language == lang)
                    percentage = (count / total_lang * 100) if total_lang > 0 else 0
                    print(f"  - {lang:<12}: {count:>4}/{total_lang:<4} entries ({percentage:>5.1f}%)")
            
            if model_counts:
                print(f"\nBreakdown by model:")
                for model, count in sorted(model_counts.items()):
                    total_model = sum(1 for r in self.db.results if r.model == model)
                    percentage = (count / total_model * 100) if total_model > 0 else 0
                    print(f"  - {model:<30}: {count:>4}/{total_model:<4} entries ({percentage:>5.1f}%)")
        else:
            total_for_lang = sum(1 for r in self.db.results if r.language.lower() == language.lower())
            print(f"Language: {language}")
            print(f"Total entries for {language}: {total_for_lang}")
            print(f"Entries matching pattern: {len(matching_results)}")
            
            # Show model breakdown even for specific language
            if model_counts:
                print(f"\nBreakdown by model for {language}:")
                for model, count in sorted(model_counts.items()):
                    total_model_lang = sum(1 for r in self.db.results 
                                         if r.model == model and r.language.lower() == language.lower())
                    percentage = (count / total_model_lang * 100) if total_model_lang > 0 else 0
                    print(f"  - {model:<30}: {count:>4}/{total_model_lang:<4} entries ({percentage:>5.1f}%)")
        
        if not matching_results:
            print("No matching entries found.")
            return 0
        
        # Show some examples
        print(f"\nExample matches (showing first 3):")
        for i, result in enumerate(matching_results[:3]):
            print(f"\n  [{i+1}] Model: {result.model}, Task: {result.task_name}")
            # Show the matching error (truncated)
            for error in result.errors:
                if pattern.search(error):
                    error_preview = error[:200] + "..." if len(error) > 200 else error
                    print(f"      Error: {error_preview}")
                    break
        
        if len(matching_results) > 3:
            print(f"\n  ... and {len(matching_results) - 3} more entries")
        
        # Confirm action
        if confirm:
            action_verb = "flag for retry" if flag_only else "remove"
            print(f"\nWARNING: This will {action_verb} {len(matching_results)} entries in the database.")
            response = input("Do you want to proceed? (y/N): ").strip().lower()
            if response != 'y':
                print("Operation cancelled.")
                return 0
        
        if flag_only:
            # Flag matching results with retry=True
            flagged = 0
            for result in matching_results:
                result.retry = True
                flagged += 1
            
            if flagged > 0:
                self.db.save_db()
                print(f"\nSuccessfully flagged {flagged} entries for retry.")
            
            return flagged
        else:
            # Remove matching results
            original_count = len(self.db.results)
            self.db.results = [r for r in self.db.results if r not in matching_results]
            
            removed = original_count - len(self.db.results)
            if removed > 0:
                self.db.save_db()
                print(f"\nSuccessfully removed {removed} entries.")
            
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
    
    def retry_task(self, task_name: str, confirm: bool = True) -> tuple[int, int]:
        """Set retry flag for all entries of a particular task and remove higher runs.
        
        For each model/language combination with multiple runs for this task:
        - Keep run 1 and set retry=True
        - Remove all higher runs (run 2, run 3, etc.)
        
        Args:
            task_name: Name of the task (e.g., "simple.json")
            confirm: Whether to ask for confirmation
            
        Returns:
            Tuple of (number flagged for retry, number removed)
        """
        from collections import defaultdict
        
        # Extract just the filename if it includes a path
        task_filename = Path(task_name).name
        
        # Find all results for this task
        task_results = [r for r in self.db.results if Path(r.task_name).name == task_filename]
        
        if not task_results:
            print(f"No results found for task '{task_filename}'")
            return 0, 0
        
        # Group results by model+language
        grouped = defaultdict(list)
        for result in task_results:
            key = (result.model, result.language)
            grouped[key].append(result)
        
        # Identify what to flag and what to remove
        to_flag = []
        to_remove = []
        
        for (model, lang), results in grouped.items():
            # Sort by run number
            results.sort(key=lambda r: r.run)
            
            if len(results) > 0:
                # Keep run 1 (or lowest run) and flag it
                to_flag.append(results[0])
                # Remove all higher runs
                to_remove.extend(results[1:])
        
        # Show statistics
        print(f"\n=== Retry Task: {task_filename} ===")
        print(f"Total entries for this task: {len(task_results)}")
        print(f"Unique model/language combinations: {len(grouped)}")
        print(f"Entries to flag for retry: {len(to_flag)}")
        print(f"Entries to remove (higher runs): {len(to_remove)}")
        
        if len(to_flag) == 0 and len(to_remove) == 0:
            print("No changes needed.")
            return 0, 0
        
        # Show examples
        if to_flag:
            print(f"\nExample entries to flag (showing first 3):")
            for i, result in enumerate(to_flag[:3]):
                print(f"  [{i+1}] {result.model} / {result.language} / run {result.run}")
            if len(to_flag) > 3:
                print(f"  ... and {len(to_flag) - 3} more")
        
        if to_remove:
            print(f"\nExample entries to remove (showing first 3):")
            for i, result in enumerate(to_remove[:3]):
                print(f"  [{i+1}] {result.model} / {result.language} / run {result.run}")
            if len(to_remove) > 3:
                print(f"  ... and {len(to_remove) - 3} more")
        
        # Confirm action
        if confirm:
            print(f"\nWARNING: This will:")
            print(f"  - Flag {len(to_flag)} entries for retry")
            print(f"  - Remove {len(to_remove)} entries (higher runs)")
            response = input("Do you want to proceed? (y/N): ").strip().lower()
            if response != 'y':
                print("Operation cancelled.")
                return 0, 0
        
        # Apply changes
        # Flag entries for retry
        for result in to_flag:
            result.retry = True
        
        # Remove higher runs
        self.db.results = [r for r in self.db.results if r not in to_remove]
        
        # Save changes
        self.db.save_db()
        print(f"\nSuccessfully flagged {len(to_flag)} entries for retry and removed {len(to_remove)} higher runs.")
        
        return len(to_flag), len(to_remove)

    def retry_language(self, language: str, model: Optional[str] = None, confirm: bool = True) -> tuple[int, int]:
        """Set retry flag for all run=1 entries for a language and remove higher runs.

        For each model/language/task_name combination with multiple runs:
        - Keep the lowest run (typically run 1) and set retry=True
        - Remove all higher runs (run 2, run 3, etc.)

        Args:
            language: Language to filter (python, rust, typescript, java, etc.)
            model: Optional model name to scope the operation
            confirm: Whether to ask for confirmation

        Returns:
            Tuple of (number flagged for retry, number removed)
        """
        from collections import defaultdict

        lang_norm = language.lower()

        # Filter results for the language (and model if provided)
        filtered_results = [
            r for r in self.db.results
            if r.language.lower() == lang_norm and (model is None or r.model == model)
        ]

        if not filtered_results:
            if model:
                print(f"No results found for language '{language}' with model '{model}'")
            else:
                print(f"No results found for language '{language}'")
            return 0, 0

        # Group by (model, language, task_name)
        grouped = defaultdict(list)
        for result in filtered_results:
            key = (result.model, result.language, Path(result.task_name).name)
            grouped[key].append(result)

        # Identify what to flag and what to remove
        to_flag: list[TestResult] = []
        to_remove: list[TestResult] = []

        for key, results in grouped.items():
            # Sort by run number
            results.sort(key=lambda r: r.run)

            # Keep the lowest run, remove the rest
            lowest = results[0]
            to_flag.append(lowest)
            to_remove.extend(results[1:])

        # Show statistics
        print(f"\n=== Retry Language: {language} ===")
        if model:
            print(f"Model scope: {model}")
        print(f"Unique model/language/task combinations: {len(grouped)}")
        print(f"Entries to flag for retry: {len(to_flag)}")
        print(f"Entries to remove (higher runs): {len(to_remove)}")

        if len(to_flag) == 0 and len(to_remove) == 0:
            print("No changes needed.")
            return 0, 0

        # Show examples
        if to_flag:
            print(f"\nExample entries to flag (showing first 3):")
            for i, result in enumerate(to_flag[:3]):
                print(f"  [{i+1}] {result.model} / {result.language} / {Path(result.task_name).name} / run {result.run}")
            if len(to_flag) > 3:
                print(f"  ... and {len(to_flag) - 3} more")

        if to_remove:
            print(f"\nExample entries to remove (showing first 3):")
            for i, result in enumerate(to_remove[:3]):
                print(f"  [{i+1}] {result.model} / {result.language} / {Path(result.task_name).name} / run {result.run}")
            if len(to_remove) > 3:
                print(f"  ... and {len(to_remove) - 3} more")

        # Confirm action
        if confirm:
            print(f"\nWARNING: This will:")
            print(f"  - Flag {len(to_flag)} entries for retry")
            print(f"  - Remove {len(to_remove)} entries (higher runs)")
            response = input("Do you want to proceed? (y/N): ").strip().lower()
            if response != 'y':
                print("Operation cancelled.")
                return 0, 0

        # Apply changes
        for result in to_flag:
            result.retry = True

        self.db.results = [r for r in self.db.results if r not in to_remove]

        # Save changes
        self.db.save_db()
        print(f"\nSuccessfully flagged {len(to_flag)} entries for retry and removed {len(to_remove)} higher runs.")

        return len(to_flag), len(to_remove)
    
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


def merge_databases_smart(
    input_files: List[str],
    output_file: str
) -> None:
    """Merge multiple databases with intelligent priority based on test success.

    Guiding principle: successful tests have priority
    - If a test only exists in one file, take it
    - If a test exists in both files, take the successful one
    - If both are successful, take from the first file
    - Handle run numbers intelligently based on success

    Args:
        input_files: List of database file paths to merge
        output_file: Path for the merged output database
    """
    from collections import defaultdict

    if not input_files:
        raise ValueError("No input files provided")

    # Load all databases
    databases = []
    for file_path in input_files:
        print(f"Loading: {file_path}")
        databases.append(ResultDB(file_path))

    # Group all results by (task_name, model, language)
    # This groups different runs together
    result_groups = defaultdict(list)

    for db_idx, db in enumerate(databases):
        for result in db.results:
            # Normalize task_name to just the filename for consistency
            normalized_task = Path(result.task_name).name
            key = (normalized_task, result.model, result.language)
            result_groups[key].append((db_idx, result))

    # Process each group and select the best result(s)
    merged_results = []

    for (task, model, language), entries in result_groups.items():
        # Separate entries by run number and source
        runs_by_number = defaultdict(list)
        for db_idx, result in entries:
            runs_by_number[result.run].append((db_idx, result))

        # Determine which runs to include
        selected_runs = {}

        # Process run 1 first (most important)
        if 1 in runs_by_number:
            run1_entries = runs_by_number[1]

            # Find if any run 1 is successful
            successful_run1 = None
            for db_idx, result in run1_entries:
                if result.success:
                    if successful_run1 is None or db_idx < successful_run1[0]:
                        # Take first successful run 1
                        successful_run1 = (db_idx, result)

            if successful_run1:
                selected_runs[1] = successful_run1[1]
            else:
                # No successful run 1, take from first file
                selected_runs[1] = run1_entries[0][1]

        # Handle higher runs
        run1_successful = 1 in selected_runs and selected_runs[1].success

        for run_num in sorted(runs_by_number.keys()):
            if run_num == 1:
                continue  # Already processed

            run_entries = runs_by_number[run_num]

            if run1_successful:
                # If run 1 is successful, we wouldn't normally have higher runs
                # Skip higher runs in this case
                continue
            else:
                # Run 1 failed or doesn't exist, consider higher runs
                # Find best entry for this run number
                successful_entry = None
                for db_idx, result in run_entries:
                    if result.success:
                        if successful_entry is None or db_idx < successful_entry[0]:
                            successful_entry = (db_idx, result)

                if successful_entry:
                    selected_runs[run_num] = successful_entry[1]
                else:
                    # Take from first file
                    selected_runs[run_num] = run_entries[0][1]

        # Special case: only run 2+ exists, no run 1
        if 1 not in selected_runs and selected_runs:
            # Find the lowest run number we have
            min_run = min(selected_runs.keys())
            if min_run > 1:
                # Renumber it to run 1
                result_to_renumber = selected_runs[min_run]
                # Create a copy with run=1
                import copy
                renumbered = copy.deepcopy(result_to_renumber)
                renumbered.run = 1
                merged_results.append(renumbered)
                # Remove the original from selected_runs
                del selected_runs[min_run]

        # Add all selected runs to merged results
        for run_num in sorted(selected_runs.keys()):
            result = selected_runs[run_num]
            # Ensure task_name is normalized
            result.task_name = task
            merged_results.append(result)

    # Create merged database
    merged_db = ResultDB(output_file)
    merged_db.results = merged_results

    # Merge costs and durations intelligently
    merged_db.costs = {}
    merged_db.durations = {}

    for db in databases:
        for model, costs in db.costs.items():
            if model not in merged_db.costs:
                merged_db.costs[model] = {}
            for lang, cost in costs.items():
                # Take the cost from the database that contributed the successful result
                if lang not in merged_db.costs[model]:
                    merged_db.costs[model][lang] = cost

        for model, durations in db.durations.items():
            if model not in merged_db.durations:
                merged_db.durations[model] = {}
            for lang, duration in durations.items():
                if lang not in merged_db.durations[model]:
                    merged_db.durations[model][lang] = duration

    merged_db.save_db()

    # Print statistics
    success_count = sum(1 for r in merged_results if r.success)
    print(f"\nMerged {len(input_files)} databases into {output_file}")
    print(f"Total results: {len(merged_results)}")
    print(f"Successful results: {success_count} ({success_count/len(merged_results)*100:.1f}%)" if merged_results else "")

    # Count unique combinations
    unique_combinations = set()
    for result in merged_results:
        unique_combinations.add((result.model, result.language, result.task_name))
    print(f"Unique model/language/task combinations: {len(unique_combinations)}")


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
    
    # Remove by error pattern command
    remove_error_parser = subparsers.add_parser(
        "remove-by-error",
        help="Remove or flag results where errors match a regex pattern"
    )
    remove_error_parser.add_argument("db", help="Database file path")
    remove_error_parser.add_argument("language", help="Language to filter (use 'all' for all languages)")
    remove_error_parser.add_argument("pattern", help="Regex pattern to match in errors")
    remove_error_parser.add_argument("--no-confirm", action="store_true", help="Skip confirmation prompt")
    remove_error_parser.add_argument("--flag", action="store_true", help="Flag entries with retry=True instead of removing them")
    
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

    # Smart merge command
    merge_smart_parser = subparsers.add_parser(
        "merge-smart",
        help="Merge databases with intelligent success-based priority"
    )
    merge_smart_parser.add_argument("-o", "--output", required=True, help="Output database file path")
    merge_smart_parser.add_argument("inputs", nargs="+", help="Input database files to merge")
    
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
    
    # Retry task command - flag a task for retry and remove higher runs
    retry_task_parser = subparsers.add_parser("retry-task", help="Flag all entries of a task for retry and remove higher runs")
    retry_task_parser.add_argument("db", help="Database file path")
    retry_task_parser.add_argument("task", help="Task name to retry (e.g., 'simple.json')")
    retry_task_parser.add_argument("--no-confirm", action="store_true", help="Skip confirmation prompt")

    # Retry language command - flag all run=1 results for a language (optionally scoped to a model) and remove higher runs
    retry_lang_parser = subparsers.add_parser(
        "retry-language",
        help="Flag all run=1 entries for a language (optionally for a specific model) for retry and remove higher runs",
    )
    retry_lang_parser.add_argument("db", help="Database file path")
    retry_lang_parser.add_argument("language", help="Language to retry (e.g., 'java')")
    retry_lang_parser.add_argument("-m", "--model", help="Optional model to scope the retry", default=None)
    retry_lang_parser.add_argument("--no-confirm", action="store_true", help="Skip confirmation prompt")
    
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
    
    elif args.command == "remove-by-error":
        tool = DBTool(args.db)
        tool.remove_by_error_pattern(args.language, args.pattern, confirm=not args.no_confirm, flag_only=args.flag)
    
    elif args.command == "merge":
        merge_databases(args.inputs, args.output, args.priority)

    elif args.command == "merge-smart":
        merge_databases_smart(args.inputs, args.output)
    
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
    
    elif args.command == "retry-task":
        tool = DBTool(args.db)
        tool.retry_task(args.task, confirm=not args.no_confirm)

    elif args.command == "retry-language":
        tool = DBTool(args.db)
        tool.retry_language(args.language, model=args.model, confirm=not args.no_confirm)


if __name__ == "__main__":
    main()
