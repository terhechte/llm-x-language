import json
import http.client
from urllib.parse import urlparse
import os
from dataclasses import dataclass


def request_openrouter(query: str, model: str, language: str):
    conn, headers, path = _get_conn("https://openrouter.ai/api/v1/chat/completions")

    # hack to enforce deepseek api for deepseek models
    # as the others are unbelievable slow
    provider = None
    if model in ["deepseek/deepseek-r1", "deepseek/deepseek-chat"]:
        provider = {"order": ["DeepSeek", "DeepInfra"]}

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
            "provider": provider,
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


@dataclass
class ModelInfo:
    name: str
    prompt_pricing: str
    completion_pricing: str


def model_info(models: list[str]) -> dict[str, ModelInfo]:
    conn, headers, path = _get_conn("https://openrouter.ai/api/v1/models")
    conn.request("GET", path, headers=headers)

    response = conn.getresponse()
    result = response.read().decode()
    r = json.loads(result)
    results = {}
    for entry in r["data"]:
        if entry["id"] not in models:
            continue
        pricing = entry["pricing"]
        prompt_pricing = pricing["prompt"]
        completion_pricing = pricing["completion"]
        results[entry["id"]] = ModelInfo(
            name=entry["id"],
            prompt_pricing=prompt_pricing,
            completion_pricing=completion_pricing,
        )
    return results


def _get_conn(url: str):
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY environment variable must be set")
    # Parse the URL to extract host and path
    parsed_url = urlparse(url)
    conn = http.client.HTTPSConnection(
        parsed_url.netloc, timeout=1400
    )  # super long timeout for reasoning models

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    return conn, headers, parsed_url.path
