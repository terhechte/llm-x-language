import http.client
from urllib.parse import urlparse
import os

from provider.types import ModelInfo
import json


def request(query: str, model: str, language: str) -> tuple[str, int, int]:
    conn, headers, path = _get_conn("https://api.together.xyz/v1/chat/completions")

    # Prepare the data to be sent in JSON format
    payload = json.dumps(
        {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": f"You are an expert {language} programmer with years of experience in coding and bug fixing. You usually detect inaccuracies in code and fix them on first sight.",
                },
                {"role": "user", "content": query},
            ],
        }
    )

    fail_counter = 0
    while True:
        if fail_counter >= 3:
            raise TimeoutError("Request timed out")
        try:
            conn.request("POST", path, body=payload, headers=headers)

            response = conn.getresponse()

            if response.status == 200:
                result = response.read().decode()
                r = json.loads(result)
                try:
                    content = r["choices"][0]["message"]["content"]
                    usage = r["usage"]
                    prompt_tokens = usage["prompt_tokens"]
                    completion_tokens = usage["completion_tokens"]
                    return content, prompt_tokens, completion_tokens
                except (KeyError, IndexError):
                    print(r)
                    fail_counter += 1
                    continue
            else:
                print(f"Error: Received status code {response.status}")
                # Print the response body for more details on errors
                print(response.read().decode())
                fail_counter += 1
                continue
        except TimeoutError:
            print("Error: TimeoutError")
            fail_counter += 1
            continue
        except (http.client.HTTPException, ConnectionError, json.JSONDecodeError) as e:
            print(f"Error: {e}")
            fail_counter += 1
            continue


def model_info(models: list[tuple[str, str]]) -> dict[str, ModelInfo]:
    conn, headers, path = _get_conn("https://api.together.xyz/v1/models")
    conn.request("GET", path, headers=headers)

    model_ids = [m[1] for m in models]

    response = conn.getresponse()
    result = response.read().decode()
    r = json.loads(result)
    results = {}
    found_models = []
    for entry in r:
        if entry["id"] not in model_ids:
            continue
        model_name = models[model_ids.index(entry["id"])][0]
        found_models.append(model_name)
        pricing = entry["pricing"]
        prompt_pricing = float(pricing["input"]) / 1_000_000
        completion_pricing = float(pricing["output"]) / 1_000_000
        results[model_name] = ModelInfo(
            name=entry["id"],
            prompt_pricing=str(prompt_pricing),
            completion_pricing=str(completion_pricing),
        )
    for model in models:
        if model[0] not in found_models:
            results[model[0]] = ModelInfo(
                name=model[0], prompt_pricing="0", completion_pricing="0"
            )
    return results


def _get_conn(url: str):
    # Determine API key based on the URL host
    parsed_url = urlparse(url)
    api_key = None
    if parsed_url.netloc == "api.together.xyz":
        api_key = os.environ.get("TOGETHER_API_KEY")
        if not api_key:
            raise ValueError(
                "TOGETHER_API_KEY environment variable must be set for Together AI API"
            )
    elif parsed_url.netloc == "openrouter.ai":  # Keep logic for model_info
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENROUTER_API_KEY environment variable must be set for OpenRouter API"
            )
    else:
        raise ValueError(f"Unsupported API host: {parsed_url.netloc}")

    conn = http.client.HTTPSConnection(parsed_url.netloc, timeout=1400)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    return conn, headers, parsed_url.path
