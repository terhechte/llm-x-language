import re
from typing import Any, Union, Dict, List, Optional, Tuple
from dataclasses import dataclass
import json

# A generic JSON value can be:
JSONValue = Union[Dict[str, Any], List[Any]]


@dataclass
class ContainsMatch:
    contains: str
    before: Optional[str]
    after: Optional[str]


@dataclass
class Result:
    success: bool
    errors: List[str]


@dataclass
class TaskResult:
    run: int
    result: Result
    response: str
    code: str
    output: str
    expected_output: str
    errors: List[str]
    tokens: Tuple[int, int]

    def __init__(
        self,
        run: int,
        success: bool,
        errors: List[str],
        response: str,
        code: str,
        output: str,
        expected_output: str | dict[str, Any] | list[Any],
        tokens: Tuple[int, int],
    ):
        self.run = run
        self.result = Result(success, errors)
        self.response = response
        self.code = code
        self.output = output
        self.errors = errors
        self.tokens = tokens
        if isinstance(expected_output, str):
            self.expected_output = expected_output
        else:
            self.expected_output = json.dumps(expected_output)

    @classmethod
    def error(cls, run: int, errors: List[str]) -> "TaskResult":
        return cls(run, False, errors, "", "", "", "", (0, 0))


def find_code_blocks_with_language(markdown: str) -> list[tuple[str, str]]:
    """
    Return a list of (language, code) tuples extracted from code blocks in 'markdown'.
    If no language is specified, the language part will be '' (empty string).
    """
    # Explanation of the pattern:
    #   ```          Matches the opening triple backticks
    #   [ \t]*       Optionally matches spaces/tabs
    #   (\S*)?       Captures zero or more non-whitespace characters as the 'language', if any
    #   .*?\n        Then we expect up to a newline (non-greedily), which ends the line with the language
    #   ([\s\S]*?)   Captures the actual code block, up until...
    #   ```          The closing triple backticks
    pattern = r"```[ \t]*(\S*)[ \t]*\n([\s\S]*?)```"

    matches = re.findall(pattern, markdown, flags=re.DOTALL)

    if len(matches) == 0:
        return []

    # Get the first block's content
    first_block_content = matches[0][1].strip()

    # Filter out blocks that are contained within the first block
    filtered_matches = [matches[0]]  # Always keep the first block
    for language, code in matches[1:]:
        if code.strip() not in first_block_content:
            filtered_matches.append((language, code))

    return filtered_matches


def are_string_values_equal(value1: str, value2: str, lowercase: bool) -> bool:
    if lowercase:
        return value1.strip().lower() == value2.strip().lower()
    else:
        return value1.strip() == value2.strip()


def are_json_values_equal(value1: JSONValue, value2: JSONValue) -> bool:
    """
    Recursively checks if two JSONValue instances are the same.
    The order of keys in dictionaries does not matter.
    """
    if isinstance(value1, dict) and isinstance(value2, dict):
        # Compare dictionaries by recursively comparing their key-value pairs
        if set(value1.keys()) != set(value2.keys()):
            return False
        return all(are_json_values_equal(value1[key], value2[key]) for key in value1)
    elif isinstance(value1, list) and isinstance(value2, list):
        # Compare lists recursively
        if len(value1) != len(value2):
            return False
        return all(
            are_json_values_equal(v1, v2)
            for v1, v2 in zip(sorted(value1, key=repr), sorted(value2, key=repr))
        )
    else:
        # Compare primitive values directly
        return value1 == value2


def check_contains_matches(text: str, matches: list[ContainsMatch], mode: str) -> bool:
    """
    Check if the text matches the given contains conditions.

    For each ContainsMatch:
      - 'contains' must appear in the text. We'll check every occurrence of 'contains'.
      - If 'before' is set, we require that 'contains' appears strictly before 'before' in the text.
      - If 'after' is set, we require that 'contains' appears strictly after 'after' in the text.

    Args:
        text: The text to search in
        matches: List of ContainsMatch conditions to check
        mode: Either "and" or "or"
            - "and": all matches must pass at least once in the text
            - "or":  at least one match must pass

    Returns:
        True if conditions are met, False otherwise
    """
    results = []

    for match in matches:
        # Find all positions where `match.contains` occurs
        start_pos = 0
        contains_positions = []
        while True:
            pos = text.find(match.contains, start_pos)
            if pos == -1:
                break
            contains_positions.append(pos)
            start_pos = pos + 1

        valid_for_this_match = False

        # Check each occurrence of `match.contains`
        for c_pos in contains_positions:
            position_valid = True

            # 1) Check "after" condition:
            #    "contains" must appear after the `match.after` substring
            if match.after is not None:
                # We look for an occurrence of `match.after` that appears *before* c_pos
                # If there's no occurrence that ends before c_pos, fail.
                after_pos = text.rfind(match.after, 0, c_pos)
                if after_pos == -1:
                    position_valid = False

            # 2) Check "before" condition:
            #    "contains" must appear before the `match.before` substring
            if match.before is not None and position_valid:
                # We look for an occurrence of `match.before` that appears *after* c_pos
                before_pos = text.find(match.before, c_pos + len(match.contains))
                if before_pos == -1:
                    position_valid = False

            # If this occurrence meets all conditions, mark success and stop checking more
            if position_valid:
                valid_for_this_match = True
                break

        results.append(valid_for_this_match)

    if mode == "and":
        return all(results)
    else:  # mode == "or"
        return any(results)
