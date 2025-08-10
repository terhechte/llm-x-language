# C# Container

This container runs C# code for the LLM benchmark framework.

## Dependencies

- .NET 8.0 SDK
- System.Text.Json for JSON serialization
- Microsoft.AspNetCore for HTTP server tasks
- Newtonsoft.Json for additional JSON support

## Structure

- `Dockerfile`: Container definition
- `csharp_container.csproj`: Project file with dependencies
- `Program.cs`: Main entry point (overwritten with generated code)

## Building

```bash
docker build -t llm-benchmark/csharp .
```

## Running

The container is designed to be run with generated code copied in at runtime.