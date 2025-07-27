# Go Container

This container provides a Go environment for executing LLM-generated Go code.

## Prerequisites

- **Go**: Version 1.19 or higher
- **goimports**: Tool for formatting Go code and managing imports

## Installation

### Installing Go

#### macOS
```bash
# Using Homebrew
brew install go

# Or download from https://go.dev/dl/
```

#### Linux
```bash
# Download and install from https://go.dev/dl/
# Or use package manager:
# Ubuntu/Debian
sudo apt-get install golang-go

# Fedora
sudo dnf install golang
```

#### Windows
Download the installer from https://go.dev/dl/

### Installing goimports

After installing Go, install goimports:
```bash
go install golang.org/x/tools/cmd/goimports@latest
```

Make sure your `$GOPATH/bin` is in your `PATH`:
```bash
export PATH=$PATH:$(go env GOPATH)/bin
```

## Dependencies

This container uses Go modules for dependency management. Dependencies are automatically downloaded when running the code.

## Usage

The benchmark framework will:
1. Write Go code to `main.go`
2. Format the code using `goimports` (or `gofmt` as fallback)
3. Run the code using `go run main.go`
4. Optionally build using `go build -o main main.go`
5. Validate code using `go vet ./...`

## Commands Used by Benchmark

- **Format**: `goimports -w main.go` (preferred) or `gofmt -w main.go` (fallback)
- **Run**: `go run main.go`
- **Build**: `go build -o main main.go`
- **Validate**: `go vet ./...`

## Notes

- The `go.mod` file defines the module name and Go version
- All dependencies are managed through Go modules
- The benchmark may use various Go standard library packages