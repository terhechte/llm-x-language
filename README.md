# LLM-X Language

go:
go install golang.org/x/tools/cmd/goimports@latest

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
