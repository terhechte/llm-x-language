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


def request(query: str, model: str, language: str) -> tuple[str, int, int]:
    if is_lmstudio_model(model):
        return request_lmstudio(query, replace_lmstudio_model(model), language)
    elif is_openrouter_model(model):
        return request_openrouter(query, replace_openrouter_model(model), language)
    elif is_together_ai_model(model):
        return request_together_ai(query, replace_together_ai_model(model), language)
    elif is_inception_model(model):
        return request_inception(query, replace_inception_model(model), language)
    else:
        raise ValueError(f"Unknown model: {model}")


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
    return {
        **model_info_openrouter(openrouter_models),
        **model_info_lmstudio(lmstudio_models),
        **model_info_together_ai(together_ai_models),
        **model_info_inception(inception_models),
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
