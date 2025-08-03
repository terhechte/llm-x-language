"""Mock provider for testing code generation without external API calls."""

from provider.types import ModelInfo


def request(query: str, model: str, language: str) -> tuple[str, int, int]:
    """
    Return predefined code based on the language.
    Returns (code, input_tokens, output_tokens)
    """
    # Mock token counts
    input_tokens = len(query.split())
    output_tokens = 50
    
    # Return simple example functions based on language
    code_map = {
        "python": "def example(input: str) -> str:\n    return input",
        "rust": "fn example(input: String) -> String {\n    input\n}",
        "typescript": "function example(input: string): string {\n    return input;\n}",
        "swift": "func example(_ input: String) -> String {\n    return input\n}",
        "kotlin": "fun example(input: String): String = input",
        "go": "func example(input string) string {\n    return input\n}",
        "php": "<?php\nfunction example($input) {\n    return $input;\n}",
        "lua": "function example(input)\n    return input\nend"
    }
    
    # Get the code for the language, default to Python if not found
    code = code_map.get(language.lower(), code_map["python"])
    
    # Wrap the code in markdown code blocks to match what the LLM would return
    response = f"Here's the example function:\n\n```{language.lower()}\n{code}\n```"
    
    return (response, input_tokens, output_tokens)


def model_info(models: list[tuple[str, str]]) -> dict[str, ModelInfo]:
    """
    Return mock model info for testing.
    """
    result = {}
    for original_name, model_name in models:
        result[original_name] = ModelInfo(
            name=model_name,
            prompt_pricing="0.0001",
            completion_pricing="0.0002"
        )
    return result