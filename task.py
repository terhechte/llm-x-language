import json
import logging
import shutil
from dataclasses import dataclass
from typing import Any, Union, Dict, List, Optional
import os
from utils import JSONValue, ContainsMatch
from enum import Enum

TASKS_DIR = "tasks"

TaskPayload = Union[str | JSONValue]


@dataclass
class TaskCall:
    prompt: str
    input_contents: str
    expected_output: TaskPayload
    filename: str = ""
    lowercase: bool = False
    is_lang_specific: bool = False


@dataclass
class TaskCheck:
    prompt: str
    filename: str = ""
    is_lang_specific: bool = False


@dataclass
class TaskContains:
    prompt: str
    matches: list[ContainsMatch]
    mode: str  # "and" | "or"
    filename: str = ""
    is_lang_specific: bool = False


@dataclass
class TaskRun:
    prompt: str
    request: str
    expected_output: TaskPayload
    filename: str = ""
    is_lang_specific: bool = False


class Language(Enum):
    RUST = "rust"
    SWIFT = "swift"
    TYPESCRIPT = "typescript"
    PYTHON = "python"

    def string_type(self) -> str:
        if self == Language.RUST:
            return "`String`"
        elif self == Language.SWIFT:
            return "`String`"
        elif self == Language.TYPESCRIPT:
            return "`string`"
        elif self == Language.PYTHON:
            return "`str`"
        else:
            return "`String`"


def read_file_contents(
    filepath: str, parse_json: bool = False
) -> Optional[Union[str, JSONValue]]:
    """
    Reads file contents, optionally parsing as JSON.
    Returns None if file cannot be read or JSON parsing fails.
    """
    try:
        with open(os.path.join(TASKS_DIR, filepath), "r", encoding="utf-8") as f:
            contents = f.read()
            return json.loads(contents) if parse_json else contents
    except (IOError, json.JSONDecodeError) as e:
        print("Error reading file %s: %s", filepath, e)
        return None


def parse_task(task_json: Dict[str, Any], prompt: str) -> Optional[TaskCall]:
    """
    Parses a task JSON into a TaskCall dataclass.
    Returns None if parsing fails.
    """
    if task_json.get("type") != "call":
        return None

    payload = task_json.get("payload", {})

    # Handle input
    input_contents: str
    if "input_file_contents" in payload:
        s = ""
        try:
            s = open(payload["input_file_contents"], "r", encoding="utf-8").read()
        except FileNotFoundError:
            return None
        if s is None:
            return None
        input_contents = s
        print(input_contents)
    elif "input_file_contents_json" in payload:
        # we disable this for now, because to simplify this benchmark, every fn has a single parameter
        # of type string
        sx = read_file_contents(payload["input_file_contents_json"], parse_json=True)
        if sx is None:
            return None
        input_contents = json.dumps(sx)
        print(input_contents)
    elif "input" in payload:
        input_contents = payload["input"]
    elif "input_file_path" in payload:
        from_path, to_path = payload["input_file_path"].split("->", maxsplit=1)
        if len(from_path.strip()) == 0 or len(to_path.strip()) == 0:
            print(f"Error: Invalid input_file_path: {payload['input_file_path']}")
            return None
        from_path = os.path.join(TASKS_DIR, from_path)
        if not os.path.exists(from_path):
            print(f"Error: Input file {from_path} does not exist")
            return None
        shutil.copy(from_path, to_path)
        input_contents = to_path
    else:
        print("Error: No valid input field found in payload")
        return None

    # Handle expected output
    expected_output: TaskPayload
    if "expected_output_file_contents" in payload:
        sy = read_file_contents(payload["expected_output_file_contents"])
        if sy is None:
            return None
        expected_output = sy
    elif "expected_output_file_contents_json" in payload:
        sy = read_file_contents(
            payload["expected_output_file_contents_json"], parse_json=True
        )
        if sy is None:
            return None
        expected_output = sy
    elif "expected_output" in payload:
        expected_output = payload["expected_output"]
    elif "expected_output_json" in payload:
        json_data = payload["expected_output_json"]
        try:
            expected_output = json.loads(json_data)
        except json.JSONDecodeError:
            logging.error("Error: Invalid JSON in expected_output_json: %s", json_data)
            return None
    else:
        print("Error: No valid expected_output field found in payload")
        return None

    # Return None if either input or output failed to parse
    if input_contents is None or expected_output is None:
        return None

    lowercase = False
    if "lowercase" in payload:
        lowercase = payload["lowercase"]

    return TaskCall(
        prompt=prompt,
        input_contents=input_contents,
        expected_output=expected_output,
        lowercase=lowercase,
    )


def parse_contains_task(
    task_json: Dict[str, Any], prompt: str
) -> Optional[TaskContains]:
    """
    Parses a contains-type task JSON into a TaskContains dataclass.
    Returns None if parsing fails.
    """
    if task_json.get("type") != "contains":
        return None

    payload = task_json.get("payload", {})

    # Handle both old and new format for backward compatibility
    if "contains" in payload:
        # Old format
        match = ContainsMatch(
            contains=payload["contains"],
            before=payload.get("before"),
            after=payload.get("after"),
        )
        matches = [match]
        mode = "and"  # Default to and for backward compatibility
    else:
        mode = "and"
        # New format
        all_matches = []
        if "matches" in payload:
            all_matches = payload["matches"]
        elif isinstance(payload, list):
            all_matches = payload
        else:
            print("Error: No 'matches' field found in payload")
            return None

        matches = []
        for match_data in all_matches:
            if "contains" not in match_data:
                print("Error: match missing 'contains' field")
                return None
            match = ContainsMatch(
                contains=match_data["contains"],
                before=match_data.get("before"),
                after=match_data.get("after"),
            )
            matches.append(match)

        if "mode" in payload:
            mode = payload["mode"]
        if mode not in ["and", "or"]:
            print("Error: mode must be either 'and' or 'or'")
            return None

    return TaskContains(
        prompt=prompt,
        matches=matches,
        mode=mode,
    )


def parse_run_task(task_json: Dict[str, Any], prompt: str) -> Optional[TaskRun]:
    """
    Parses a run-type task JSON into a TaskRun dataclass.
    Returns None if parsing fails.
    """
    if task_json.get("type") != "run":
        return None

    payload = task_json.get("payload", {})

    # Check for required fields
    if "request" not in payload:
        print("Error: No 'request' field found in payload")
        return None
    if "expected_output" not in payload:
        print("Error: No 'expected_output' field found in payload")
        return None

    # Parse expected_output as JSON if it's a string
    expected_output = payload["expected_output"]
    if isinstance(expected_output, str):
        try:
            expected_output = json.loads(expected_output)
        except json.JSONDecodeError:
            # If it's not valid JSON, keep it as a string
            pass

    return TaskRun(
        prompt=prompt, request=payload["request"], expected_output=expected_output
    )


def parse_check_task(task_json: Dict[str, Any], prompt: str) -> Optional[TaskCheck]:
    if task_json.get("type") != "checks":
        return None

    return TaskCheck(prompt=prompt)


def parse_task_from_file(
    json_filepath: str,
    language: Language,
) -> Optional[Union[TaskCall, TaskContains, TaskRun, TaskCheck]]:
    """
    Reads a task JSON file and parses it into the appropriate task dataclass.
    The prompt is read from a corresponding .md file with the same base name.
    Returns None if parsing fails.
    """
    # Read and parse the JSON file
    with open(json_filepath, "r", encoding="utf-8") as f:
        contents = f.read()
        task_json = json.loads(contents)

    if task_json is None:
        print("Error: Task JSON is None")
        return None

    # Ensure task_json is a dictionary
    if not isinstance(task_json, dict):
        print("Error: Task JSON must be a dictionary")
        return None

    # Get the corresponding .md file path and read the prompt
    md_filepath = json_filepath.rsplit(".json", 1)[0] + ".md"
    prompt = open(md_filepath, "r", encoding="utf-8").read()
    if prompt is None:
        print("Error: Could not read prompt file %s", md_filepath)
        return None
    prompt = process_prompt(prompt, language, task_json["type"])

    # Parse based on type
    task_type = task_json.get("type")
    if task_type == "run":
        return parse_run_task(task_json, prompt)
    elif task_type == "call":
        return parse_task(task_json, prompt)
    elif task_type == "contains":
        return parse_contains_task(task_json, prompt)
    elif task_type == "checks":
        return parse_check_task(task_json, prompt)
    else:
        print(f"Error: Unknown task type '{task_type}'")
        return None


def load_all_tasks(
    language: Language,
    skip_lang_specific: bool,
) -> List[Union[TaskCall, TaskContains, TaskRun, TaskCheck]]:
    """
    Iterates through 'tasks' and 'tasks/rust' directories and parses all JSON files
    into task objects using parse_task_from_file.
    Returns a list of successfully parsed tasks.
    """
    tasks = []
    task_dirs = [TASKS_DIR]
    lang_specific_dir = os.path.join(TASKS_DIR, language.value)
    if not skip_lang_specific:
        task_dirs.append(lang_specific_dir)

    for directory in task_dirs:
        if not os.path.exists(directory):
            continue

        for filename in os.listdir(directory):
            if not filename.endswith(".json"):
                continue

            filepath = os.path.join(directory, filename)
            print(f"Parsing task: {filepath}")
            task = parse_task_from_file(filepath, language)
            if task is not None:
                task.filename = filename
                if directory == lang_specific_dir:
                    task.is_lang_specific = True
                tasks.append(task)

    return tasks


def process_prompt(prompt: str, language: Language, task_type: str) -> str:
    """
    Process a prompt by:
    1. Replacing {{lang}} with the global language variable
    2. Appending contents of tasks/base.md
    3. If language is rust or swift, appending contents of tasks/add_{language}.md
    Returns the processed prompt string.
    """

    string_type = language.string_type()

    # Replace {{lang}} with actual language
    processed_prompt = _process_prompt(prompt, string_type, language)
    # Append base.md contents
    base_content = open(
        os.path.join(TASKS_DIR, "base.md"), "r", encoding="utf-8"
    ).read()
    if base_content is not None:
        processed_prompt += "\n\n" + _process_prompt(
            base_content, string_type, language
        )

    # Handle language-specific additions
    # Add base language content
    lang_content = open(
        os.path.join(TASKS_DIR, f"{language.value}/_add.md"), "r", encoding="utf-8"
    ).read()
    if lang_content is not None:
        processed_prompt += "\n\n" + _process_prompt(
            lang_content, string_type, language
        )

    # Add task-specific content
    task_files = {
        "call": f"{language.value}/_task_call.md",
        "run": f"{language.value}/_task_run.md",
        "check": f"{language.value}/_task_check.md",
    }

    if task_type in task_files:
        task_content = open(
            os.path.join(TASKS_DIR, task_files[task_type]), "r", encoding="utf-8"
        ).read()
        if task_content is not None:
            processed_prompt += "\n\n" + _process_prompt(
                task_content, string_type, language
            )

    return processed_prompt


def _process_prompt(prompt: str, string_type: str, language: Language) -> str:
    processed_prompt = prompt.replace("{{lang}}", language.value)
    processed_prompt = processed_prompt.replace("{{string_type}}", string_type)
    return processed_prompt
