# LLM-X Language

go:
go install golang.org/x/tools/cmd/goimports@latest

This is a benchmark to compare different LLMs against different languages.

## Languages

```
-  SWIFT,
-  RUST,
-  TYPESCRIPT,
-  PYTHON,
-  PHP,
-  GO,
-  LUA,
-  KOTLIN,
-  CSHARP,
-  CPP,
-  JAVA,
-  ZIG,
-  SCALA,
```

## LLMs

```
        "openrouter/qwen/qwen3-30b-a3b",
        "lmstudio/deepcogito_cogito-v1-preview-qwen-32b",
        "openrouter/openai/gpt-4.1-mini",
        "openrouter/openai/gpt-4.1",
        "openrouter/openai/gpt-4.1-nano",
        "openrouter/google/gemini-2.5-pro-preview-03-25",
        "openrouter/openai/o4-mini",
        "openrouter/google/gemini-2.0-flash-001",
        "openrouter/all-hands/openhands-lm-32b-v0.1",
        "openrouter/mistral/ministral-8b",
        "inception/mercury-coder-small",
        "togetherai/deepcogito/cogito-v1-preview-llama-70B",
        "togetherai/deepcogito/deepcogito/cogito-v1-preview-qwen-32B",
        "togetherai/deepcogito/cogito-v1-preview-qwen-14B",
        "openrouter/x-ai/grok-3-mini-beta",
        "openrouter/x-ai/grok-3-beta",
        "openrouter/nvidia/llama-3.1-nemotron-ultra-253b-v1:free",
        "openrouter/meta-llama/llama-4-maverick",
        "openrouter/meta-llama/llama-4-scout",
        "openrouter/quasar-alpha",
        "openrouter/qwen/qwen-2.5-coder-32b-instruct",
        "openrouter/qwen/qwen-2.5-72b-instruct",
        "openrouter/qwen/qwen-2.5-vl-72b-instruct",
        "openrouter/qwen/qwen2.5-vl-32b-instruct:free",
        "openrouter/cognitivecomputations/dolphin3.0-mistral-24b:free",
        "openrouter/google/gemini-2.5-pro-exp-03-25:free",
        "openrouter/qwen/qwen2.5-vl-32b-instruct:free",
        "openrouter/deepseek/deepseek-chat-v3-0324",
        "openrouter/featherless/qwerky-72b:free",
        "openrouter/mistralai/mistral-small-3.1-24b-instruct",
        "openrouter/open-r1/olympiccoder-7b:free",
        "openrouter/open-r1/olympiccoder-32b:free",
        "openrouter/steelskull/l3.3-electra-r1-70b",
        "openrouter/allenai/olmo-2-0325-32b-instruct",
        "openrouter/google/gemma-3-12b-it",
        "openrouter/cohere/command-a",
        "openrouter/rekaai/reka-flash-3:free",
        "openrouter/google/gemma-3-27b-it",
        "openrouter/thedrummer/anubis-pro-105b-v1",
        "openrouter/microsoft/phi-4-multimodal-instruct",
        "openrouter/qwen/qwq-32b",
        "openrouter/openai/o3-mini",
        "openrouter/qwen/qwen-turbo",
        "openrouter/qwen/qwen-plus",
        "openrouter/qwen/qwen-max",
        "openrouter/deepseek/deepseek-r1",
        "openrouter/deepseek/deepseek-chat",
        "openrouter/openai/o1-preview",
        "openrouter/deepseek/deepseek-r1-distill-llama-70b",
        "openrouter/mistralai/codestral-2501",
        "openrouter/microsoft/phi-4",
        "openrouter/meta-llama/llama-3.3-70b-instruct",
        "openrouter/amazon/nova-pro-v1",
        "openrouter/qwen/qwq-32b-preview",
        "openrouter/openai/gpt-4o-2024-11-20",
        "openrouter/mistralai/mistral-large-2411",
        "openrouter/anthropic/claude-3.5-haiku-20241022:beta",
        "openrouter/anthropic/claude-3.5-sonnet-20240620:beta",
        "openrouter/anthropic/claude-3.7-sonnet",
        "openrouter/openai/gpt-4o-mini",
        "openrouter/openai/gpt-4o",
        "openrouter/mistralai/mistral-small-24b-instruct-2501",
        "openrouter/qwen/qwen3-next-80b-a3b-thinking",
        "openrouter/qwen/qwen3-next-80b-a3b-instruct",
        "openrouter/moonshotai/kimi-k2-0905",
        "openrouter/x-ai/grok-code-fast-1",
        "qwen/qwen3-next-80b-a3b-thinking",
        "openrouter/openai/gpt-oss-20b",
        "openrouter/z-ai/glm-4-32b",
        "openrouter/mistralai/devstral-medium",
        "openrouter/google/gemini-2.5-pro",
        "openrouter/qwen/qwen3-30b-a3b-instruct-2507",
        "openrouter/z-ai/glm-4.5",
        "openrouter/z-ai/glm-4.5-air",
        "openrouter/qwen/qwen3-235b-a22b-thinking-2507",
        "openrouter/qwen/qwen3-235b-a22b-2507",
        "openrouter/moonshotai/kimi-k2",
        "openrouter/anthropic/claude-opus-4.1",
        "openrouter/anthropic/claude-haiku-4.5",
        "openrouter/openai/gpt-5-codex",
        "openrouter/anthropic/claude-sonnet-4.5",
        "openrouter/mistralai/codestral-2508",
        "openrouter/qwen/qwen3-coder",
        "openrouter/google/gemini-2.5-flash-lite",
        "openrouter/openai/gpt-5",
        "openrouter/x-ai/grok-4"
        "openrouter/openai/gpt-oss-120b",

```

(Note, recent results with the models above haven't been published yet)

## Results

The results can be found in this blog post which also explains more about the underlying methodology.

[LLM-Powered Programming: A Language Matrix Revealed](https://ben.terhech.de/posts/2025-01-31-llms-vs-programming-languages.html)

## Setup

```bash
cp .env.example .env
# edit .env, add openrouter api key
```

## Docker Support

The framework now supports running all benchmarks in Docker containers, eliminating the need to install language runtimes locally.

### Quick Start with Docker

```bash
# Build all Docker images
./build_docker.sh

# Run benchmarks with Docker
export LLM_BENCHMARK_USE_DOCKER=true
python main.py --model_name "gpt-4o"
```

See [DOCKER.md](DOCKER.md) for detailed Docker documentation.

## Database Management

The `dbtool.py` utility provides comprehensive database management capabilities for benchmark results.

### Available Operations

```bash
# Remove all results for a specific model
python dbtool.py remove-model results/run_2025_01_15.json "gpt-4o"

# Remove all results for a specific language
python dbtool.py remove-language results/run_2025_01_15.json python

# Remove all results for a specific task (all runs)
python dbtool.py remove-task results/run_2025_01_15.json "task_001"

# Remove results for a specific language and task type
python dbtool.py remove-lang-type results/run_2025_01_15.json python call

# Merge multiple databases into one
# Priority "first" keeps first occurrence of duplicates (default)
python dbtool.py merge -o results/merged.json results/db1.json results/db2.json results/db3.json

# Priority "last" overwrites with last occurrence
python dbtool.py merge -o results/merged.json -p last results/db1.json results/db2.json

# List available items in database
python dbtool.py list results/database.json models      # List all models
python dbtool.py list results/database.json languages   # List all languages
python dbtool.py list results/database.json tasks       # List all tasks
python dbtool.py list results/database.json task-types  # List all task types

# View database statistics
python dbtool.py stats results/database.json
```

### Use Cases

- **Cleaning data**: Remove failed or incomplete test runs for specific models
- **Filtering results**: Extract results for specific languages or task types
- **Merging runs**: Combine multiple benchmark runs into a single analysis file
- **Data exploration**: List and analyze what's in your result databases
