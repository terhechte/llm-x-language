import http.client
import json
import os
from urllib.parse import urlparse

from provider.types import ModelInfo


def request(query: str, model: str, language: str) -> tuple[str, int, int]:
    """
    Sends a request to the Inception Labs API and retrieves the response.

    Args:
        query: The user's query.
        model: The model ID to use (e.g., "mercury-coder-small").
        language: The programming language context.

    Returns:
        A tuple containing the response content, prompt tokens, and completion tokens.

    Raises:
        ValueError: If the INCEPTION_API_KEY environment variable is not set.
        TimeoutError: If the request times out after multiple retries.
        RuntimeError: If the API returns an error or unexpected response.
    """
    api_key = os.environ.get("INCEPTION_API_KEY")
    if not api_key:
        raise ValueError("INCEPTION_API_KEY environment variable must be set")

    url = "https://api.inceptionlabs.ai/v1/chat/completions"
    parsed_url = urlparse(url)
    conn = http.client.HTTPSConnection(
        parsed_url.netloc, timeout=140
    )  # Standard timeout

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    # Prepare the data to be sent in JSON format
    # Including a system prompt similar to the together_ai provider
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
            # Assuming Inception might support usage reporting like OpenAI/Together
            # "usage": True # This might need adjustment based on actual API behavior
        }
    )

    fail_counter = 0
    while True:
        if fail_counter >= 3:
            raise TimeoutError("Request timed out after 3 attempts")
        try:
            conn.request("POST", parsed_url.path, body=payload, headers=headers)
            response = conn.getresponse()
            response_body = response.read().decode()

            if response.status == 200:
                try:
                    r = json.loads(response_body)
                    content = r["choices"][0]["message"]["content"]
                    # Attempt to get usage info, default to 0 if not present
                    usage = r.get("usage", {})
                    prompt_tokens = usage.get("prompt_tokens", 0)
                    completion_tokens = usage.get("completion_tokens", 0)
                    conn.close()
                    return content, prompt_tokens, completion_tokens
                except (KeyError, IndexError, json.JSONDecodeError) as e:
                    print(f"Error parsing response: {e}")
                    print(f"Response body: {response_body}")
                    fail_counter += 1
                    # Consider closing connection here if retrying
                    conn.close()
                    # Re-establish connection for retry
                    conn = http.client.HTTPSConnection(parsed_url.netloc, timeout=140)
                    continue
            else:
                print(f"Error: Received status code {response.status}")
                print(f"Response body: {response_body}")
                fail_counter += 1
                conn.close()
                # Re-establish connection for retry
                conn = http.client.HTTPSConnection(parsed_url.netloc, timeout=140)
                continue

        except TimeoutError:
            print("Error: Request timed out")
            fail_counter += 1
            conn.close()  # Close connection on timeout
            # Re-establish connection for retry
            conn = http.client.HTTPSConnection(parsed_url.netloc, timeout=140)
            continue
        except (http.client.HTTPException, ConnectionError) as e:
            print(f"HTTP/Connection Error: {e}")
            fail_counter += 1
            # Ensure connection is closed and potentially re-established if needed
            try:
                conn.close()
            except Exception:  # Ignore errors during close
                pass
            conn = http.client.HTTPSConnection(parsed_url.netloc, timeout=140)
            continue
        finally:
            # Ensure connection is closed if it's still open and no retry is happening
            # Check if fail_counter < 3 to avoid closing before retry logic can re-open
            # This finally block might need refinement based on retry logic flow
            if fail_counter >= 3 or response.status == 200:
                try:
                    if conn.sock:  # Check if connection is still open
                        conn.close()
                except Exception:
                    pass  # Ignore errors during final close attempt


def model_info(models: list[tuple[str, str]]) -> dict[str, ModelInfo]:
    """
    Provides model information for Inception Labs models.
    Since there's only one known model ("mercury-coder-small") and no public pricing,
    it returns hardcoded info for that model if requested.

    Args:
        models: A list of tuples, where each tuple contains a user-friendly
                name and the model ID (e.g., [("inception-mercury", "mercury-coder-small")]).

    Returns:
        A dictionary mapping the user-friendly model name to its ModelInfo object.
    """
    results = {}
    inception_model_id = "mercury-coder-small"
    inception_model_name = None

    # Find the user-friendly name associated with the inception model ID
    for name, model_id in models:
        if model_id == inception_model_id:
            inception_model_name = name
            break

    # If the specific Inception model was requested, provide its info
    if inception_model_name:
        results[inception_model_name] = ModelInfo(
            name=inception_model_id,
            prompt_pricing="0",  # No pricing info available
            completion_pricing="0",  # No pricing info available
        )

    # Handle cases where other models might be requested but aren't Inception's
    for name, model_id in models:
        if name not in results:
            # Indicate unknown/unsupported models if necessary, or just ignore
            # For simplicity, we'll just return info for the known model if requested.
            pass

    return results
