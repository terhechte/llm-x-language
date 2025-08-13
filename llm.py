from provider.openrouter import (
    request as request_openrouter,
    model_info as model_info_openrouter,
)
from provider.lmstudio import (
    request as request_lmstudio,
    model_info as model_info_lmstudio,
)
from provider.together_ai import (
    request as request_together_ai,
    model_info as model_info_together_ai,
)
from provider.inception import (
    request as request_inception,
    model_info as model_info_inception,
)
from provider.mock import (
    request as request_mock,
    model_info as model_info_mock,
)

from provider.types import ModelInfo


def is_lmstudio_model(model: str) -> bool:
    return model.startswith("lmstudio/")


def replace_lmstudio_model(model: str) -> str:
    return model.replace("lmstudio/", "")


def is_openrouter_model(model: str) -> bool:
    return model.startswith("openrouter/")


def replace_openrouter_model(model: str) -> str:
    return model.replace("openrouter/", "")


def is_together_ai_model(model: str) -> bool:
    return model.startswith("togetherai/")


def replace_together_ai_model(model: str) -> str:
    return model.replace("togetherai/", "")


def is_inception_model(model: str) -> bool:
    return model.startswith("inception/")


def replace_inception_model(model: str) -> str:
    return model.replace("inception/", "")


def is_mock_model(model: str) -> bool:
    return model.startswith("mock/")


def replace_mock_model(model: str) -> str:
    return model.replace("mock/", "")


def request(query: str, model: str, language: str) -> tuple[str, int, int]:
    if is_lmstudio_model(model):
        result = request_lmstudio(query, replace_lmstudio_model(model), language)
        if result is None:
            raise ValueError("LMStudio request failed")
        return result
    elif is_openrouter_model(model):
        return request_openrouter(query, replace_openrouter_model(model), language)
    elif is_together_ai_model(model):
        return request_together_ai(query, replace_together_ai_model(model), language)
    elif is_inception_model(model):
        return request_inception(query, replace_inception_model(model), language)
    elif is_mock_model(model):
        return request_mock(query, replace_mock_model(model), language)
    else:
        raise ValueError(f"Unknown model: {model}")


def request_retry(original_prompt: str, generated_code: str, error_message: str, model: str, language: str) -> tuple[str, int, int]:
    """
    Request a retry from the LLM with error feedback.
    Only works with openrouter and lmstudio providers.
    
    Args:
        original_prompt: The original task prompt
        generated_code: The code that was generated but failed
        error_message: The error message from the failed attempt
        model: The model to use for the retry
        language: The programming language
        
    Returns:
        Tuple of (response, prompt_tokens, completion_tokens)
    """
    # Only support openrouter and lmstudio models
    if not (is_openrouter_model(model) or is_lmstudio_model(model)):
        raise ValueError(f"Retry not supported for model: {model}")
    
    # Construct the retry prompt
    retry_prompt = f"""I gave you this task:

{original_prompt}

And you generated this code:

{generated_code}

but it failed with the following error:

{error_message}

Can you please update the code so it works?"""
    
    # Make the retry request using the standard request function
    return request(retry_prompt, model, language)


def model_info(models: list[str]) -> dict[str, ModelInfo]:
    openrouter_models = [
        (m, replace_openrouter_model(m)) for m in models if is_openrouter_model(m)
    ]
    lmstudio_models = [
        (m, replace_lmstudio_model(m)) for m in models if is_lmstudio_model(m)
    ]
    together_ai_models = [
        (m, replace_together_ai_model(m)) for m in models if is_together_ai_model(m)
    ]
    inception_models = [
        (m, replace_inception_model(m)) for m in models if is_inception_model(m)
    ]
    mock_models = [
        (m, replace_mock_model(m)) for m in models if is_mock_model(m)
    ]
    return {
        **model_info_openrouter(openrouter_models),
        **model_info_lmstudio(lmstudio_models),
        **model_info_together_ai(together_ai_models),
        **model_info_inception(inception_models),
        **model_info_mock(mock_models),
    }


if __name__ == "__main__":
    print(
        model_info(
            [
                "togetherai/mistralai/Mistral-7B-Instruct-v0.3",
                "openrouter/openai/gpt-4o-2024-11-20",
                "inception/mercury-coder-small",
            ]
        )
    )
