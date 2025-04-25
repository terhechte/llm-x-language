import json
import http.client
from urllib.parse import urlparse
from provider.types import ModelInfo


def request(query: str, model: str, language: str):
    parsed_url = urlparse("http://localhost:1234")
    conn = http.client.HTTPConnection(parsed_url.netloc, timeout=1400)
    headers = {
        "Content-Type": "application/json",
    }

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
            "stream": False,
        }
    )

    fail_counter = 0
    max_attempts = 3

    while True:
        if fail_counter >= max_attempts:
            print(f"Max attempts ({max_attempts}) reached. Giving up.")
            return None

        try:
            conn.request("POST", "/v1/chat/completions", body=payload, headers=headers)
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
                except (KeyError, IndexError) as e:
                    print(f"Failed to parse response: {e}")
                    fail_counter += 1
            else:
                print(f"Error: Received status code {response.status}")
                fail_counter += 1
        except (http.client.HTTPException, ConnectionError, json.JSONDecodeError) as e:
            print(f"Request failed with error: {e}")
            fail_counter += 1
        finally:
            conn.close()


def model_info(models: list[tuple[str, str]]) -> dict[str, ModelInfo]:
    return {
        k[0]: ModelInfo(name=k[1], prompt_pricing="0", completion_pricing="0")
        for k in models
    }
