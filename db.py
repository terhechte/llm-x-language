import json
from dataclasses import dataclass, asdict
from typing import List
from pathlib import Path
from datetime import datetime
from task import Language
from utils import Result
from decimal import Decimal


@dataclass
class TestResult:
    """Represents a single test result entry in the database"""

    model: str
    run: int
    task_name: str
    prompt: str
    code: str
    success: bool
    errors: List[str]
    task_type: str
    response: str
    output: str
    expected_output: str
    language: str
    cost: str
    duration: float
    is_lang_specific: bool

    @classmethod
    def from_dict(cls, data: dict) -> "TestResult":
        return cls(**data)


class ResultDB:
    def __init__(self, filename: str | None = None):
        if filename is not None:
            self.db_path = Path(filename)
        else:
            current_time = datetime.now().strftime("results/run_%Y_%m_%d_%H_%M.json")
            self.db_path = Path(current_time)
        self.results: list[TestResult] = []
        self.costs = dict[str, dict[str, Decimal]]()
        self.durations = dict[str, dict[str, float]]()
        self._load_db()

    def _load_db(self) -> None:
        """Load existing results from the JSON file if it exists"""
        if self.db_path.exists():
            try:
                print(f"Loading database from {self.db_path}")
                with open(self.db_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.costs = {
                        model: {lang: cost for lang, cost in costs.items()}
                        for model, costs in data.get("costs", {}).items()
                    }
                    self.durations = data.get("durations", {})
                    self.results = [
                        TestResult.from_dict(item) for item in data.get("results", [])
                    ]
            except json.JSONDecodeError:
                self.results = []
                self.costs = {}
                self.durations = {}

    def save_db(self) -> None:
        """Save current results to the JSON file"""
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "costs": self.costs,
                    "durations": self.durations,
                    "results": [asdict(result) for result in self.results],
                },
                f,
                indent=2,
            )

    def add_result(
        self,
        result: Result,
        model: str,
        task_name: str,
        prompt: str,
        code: str,
        run: int,
        task_type: str,
        response: str,
        output: str,
        expected_output: str,
        language: Language,
        errors: List[str],
        cost: Decimal,
        duration: float,
        is_lang_specific: bool,
    ) -> None:
        """Add a new test result to the database"""
        test_result = TestResult(
            model=model,
            run=run,
            task_name=task_name,
            prompt=prompt,
            code=code,
            success=result.success,
            errors=result.errors + errors,
            task_type=task_type,
            response=response,
            output=output,
            expected_output=expected_output,
            language=language.value,
            cost=str(cost),
            duration=duration,
            is_lang_specific=is_lang_specific,
        )
        self.results.append(test_result)
        self.save_db()

    def set_total_costs(self, model: str, language: str, costs: Decimal) -> None:
        self.costs.setdefault(model, {}).setdefault(language, "0")
        self.costs[model][language] = str(costs)

    def set_total_duration(self, model: str, language: str, duration: float) -> None:
        self.durations.setdefault(model, {}).setdefault(language, 0)
        self.durations[model][language] = duration

    def analyze(self) -> str:
        """Analyze results and return statistics in ASCII table format per model and run"""
        # Collect statistics
        stats = {}
        for result in self.results:
            key = (result.model, result.run)
            if key not in stats:
                stats[key] = {"success": 0, "failure": 0}

            if result.success:
                stats[key]["success"] += 1
            else:
                stats[key]["failure"] += 1

        # Create ASCII table
        if not stats:
            return "No results found in database."

        # Find the longest model name for formatting
        max_model_len = max(len(key[0]) for key in stats.keys())

        # Create table header
        header = f"| {'Model':<{max_model_len}} | Run | Success | Failure |"
        separator = f"|{'-' * (max_model_len + 2)}|--------|---------|----------|"

        # Create table rows
        rows = []
        for (model, run), counts in sorted(stats.items()):
            row = f"| {model:<{max_model_len}} | {run:^6} | {counts['success']:^7} | {counts['failure']:^8} |"
            rows.append(row)

        # Combine all parts
        table = "\n".join([header, separator] + rows)
        return table

    def has_result(self, run: int, task_name: str, model: str, language: str) -> bool:
        """
        Check if a result already exists in the database.

        Args:
            run: The run number to check
            task_name: The name of the task
            model: The model name
            language: The programming language

        Returns:
            bool: True if a matching result exists, False otherwise
        """
        return any(
            result.run == run
            and result.task_name == task_name
            and result.model == model
            and result.language == language
            for result in self.results
        )

    def merge_with(self, other_db: "ResultDB") -> None:
        """Merge another ResultDB instance into this one.

        Args:
            other_db: Another ResultDB instance to merge from
        """
        # Merge costs
        for model, costs in other_db.costs.items():
            if model not in self.costs:
                self.costs[model] = {}
            for lang, cost in costs.items():
                # Sum the costs if they exist in both DBs
                current_cost = Decimal(self.costs.get(model, {}).get(lang, "0"))
                other_cost = Decimal(cost)
                self.costs[model][lang] = str(
                    Decimal(current_cost) + Decimal(other_cost)
                )

        # Merge durations
        for model, durations in other_db.durations.items():
            if model not in self.durations:
                self.durations[model] = {}
            for lang, duration in durations.items():
                # Sum the durations if they exist in both DBs
                current_duration = self.durations.get(model, {}).get(lang, 0.0)
                self.durations[model][lang] = current_duration + duration

        # Merge results (avoiding duplicates based on run, task_name, model, and language)
        for result in other_db.results:
            if not self.has_result(
                result.run, result.task_name, result.model, result.language
            ):
                self.results.append(result)

        # Save the merged database
        self.save_db()

    @classmethod
    def merge_files(cls, files: list[str], output_file: str) -> None:
        """Merge multiple database files into a new file.

        Args:
            files: List of paths to database files to merge
            output_file: Path where the merged database should be saved
        """
        if not files:
            raise ValueError("No input files provided")

        # Create a new DB with the output filename
        merged_db = cls(output_file)

        # Merge all DBs into the new one
        for file in files:
            dbx = cls(file)
            merged_db.merge_with(dbx)
        merged_db.save_db()

    def print_model_runs(self) -> str:
        """Print all unique models and their highest run number.

        Returns:
            str: Formatted table showing models and their maximum run numbers
        """
        # Collect max run for each model
        model_runs = {}
        for result in self.results:
            if result.model not in model_runs:
                model_runs[result.model] = result.run
            else:
                model_runs[result.model] = max(model_runs[result.model], result.run)

        if not model_runs:
            return "No results found in database."

        # Find the longest model name for formatting
        max_model_len = max(len(model) for model in model_runs.keys())

        # Create table header
        header = f"| {'Model':<{max_model_len}} | Max Run |"
        separator = f"|{'-' * (max_model_len + 2)}|---------|"

        # Create table rows
        rows = []
        for model, max_run in sorted(model_runs.items()):
            row = f"| {model:<{max_model_len}} | {max_run:^7} |"
            rows.append(row)

        # Combine all parts
        table = "\n".join([header, separator] + rows)
        return table

    def export_aggregated(self) -> list[dict]:
        """Export aggregated statistics for each model as a list of JSON objects."""

        def calculate_success_rate(results) -> float:
            if not results:
                return 0.0
            successes = sum(1 for r in results if r.success)
            return (successes / len(results)) * 100

        def calculate_weighted_quality(results) -> float:
            if not results:
                return 0.0

            weights = {1: 1.0, 2: 0.5, 3: 0.25}  # Run weights
            default_weight = 0.15

            total_weight = 0.0
            weighted_sum = 0.0

            for result in results:
                weight = weights.get(result.run, default_weight)
                weighted_sum += weight * (1 if result.success else 0)
                total_weight += weight

            return (weighted_sum / total_weight) * 100 if total_weight > 0 else 0

        # Group results by model
        model_stats = {}
        languages = ["python", "rust", "typescript", "swift"]

        for result in self.results:
            if result.model not in model_stats:
                model_stats[result.model] = {"name": result.model, "results": []}
            model_stats[result.model]["results"].append(result)

        # Calculate statistics for each model
        aggregated_stats = []
        for model, data in model_stats.items():
            stats = {"name": model}

            for lang in languages:
                # Filter results for this language
                lang_results = [
                    r for r in data["results"] if r.language.lower() == lang
                ]
                non_specific_results = [
                    r for r in lang_results if not r.is_lang_specific
                ]

                # Calculate success rates
                stats[lang] = calculate_success_rate(lang_results)
                stats[f"{lang}-only"] = calculate_success_rate(non_specific_results)

                # Calculate average duration and costs per run
                max_runs = max((r.run for r in lang_results), default=1)
                total_duration = sum(float(r.duration) for r in lang_results)
                total_costs = sum(Decimal(r.cost) for r in lang_results)

                stats[f"{lang}-duration"] = total_duration / max_runs
                stats[f"{lang}-costs"] = float(total_costs / Decimal(max_runs))

                # Calculate quality score for this language
                stats[f"{lang}-quality"] = calculate_weighted_quality(lang_results)

                stats[f"{lang}-success-r1"] = sum(
                    1 for r in lang_results if r.run == 1 and r.success
                )
                stats[f"{lang}-success-r2"] = sum(
                    1 for r in lang_results if r.run == 2 and r.success
                )
                stats[f"{lang}-success-r3"] = sum(
                    1 for r in lang_results if r.run == 3 and r.success
                )

            aggregated_stats.append(stats)

        # Sort aggregated stats by model name
        aggregated_stats.sort(key=lambda x: x["name"])
        return aggregated_stats


