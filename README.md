# LLM-X Language

This is a benchmark to compare different LLMs against different languages.

## Languages

- Rust
- Python
- TypeScript
- Swift

## LLMs

- amazon/nova-pro-v1
- anthropic/claude-3.5-haiku-20241022:beta
- anthropic/claude-3.5-sonnet:beta
- deepseek/deepseek-chat
- deepseek/deepseek-r1
- deepseek/deepseek-r1-distill-llama-70b
- meta-llama/llama-3.3-70b-instruct
- microsoft/phi-4
- mistralai/codestral-2501
- mistralai/mistral-large-2411
- mistralai/mistral-small-24b-instruct-2501
- openai/gpt-4o-2024-11-20
- openai/gpt-4o-mini
- openai/o3-mini
- qwen/qwen-max
- qwen/qwen-plus
- qwen/qwen-turbo
- qwen/qwq-32b-preview

## Results

The results can be found in this blog post which also explains more about the underlying methodology.

[LLM-Powered Programming: A Language Matrix Revealed](https://ben.terhech.de/posts/2025-01-31-llms-vs-programming-languages.html)

## Setup

```bash
cp .env.example .env
# edit .env, add openrouter api key
```
