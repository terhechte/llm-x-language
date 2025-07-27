# Swift Container

This container provides a Swift environment for executing LLM-generated Swift code.

## Prerequisites

- **Swift**: Version 5.0 or higher
- **Swift Package Manager**: Included with Swift installation

## Installation

### Installing Swift

#### macOS
Swift comes pre-installed on macOS with Xcode:
```bash
# Install Xcode from the Mac App Store
# Or install just the command line tools:
xcode-select --install

# Verify installation
swift --version
```

#### Linux
```bash
# Ubuntu/Debian
# Add Swift repository
wget -q -O - https://swift.org/keys/all-keys.asc | sudo apt-key add -
sudo apt-get update
sudo apt-get install swift

# Or download from https://swift.org/download/
```

#### Windows
Download the installer from https://swift.org/download/

### Alternative Installation (macOS)
```bash
# Using Homebrew
brew install swift
```

## Dependencies

Dependencies are managed through `Package.swift` using Swift Package Manager (SPM). Dependencies are automatically resolved and downloaded when building the project.

## Usage

The benchmark framework will:
1. Write Swift code to `Sources/main.swift`
2. Build the project using `swift build`
3. Run the executable using `swift run`

## Commands Used by Benchmark

- **Build**: `swift build`
- **Run**: `swift run`
- **Clean**: `swift package clean`
- **Update Dependencies**: `swift package update`

## Project Structure

```
swift_container/
├── Package.swift    # Package manifest and dependencies
└── Sources/
    └── main.swift   # Main source file (replaced during benchmark)
```

## Package.swift Configuration

The `Package.swift` file defines:
- Package name and Swift version
- Executable target
- External dependencies (if needed)
- Build settings

## Notes

- Swift Package Manager handles all dependency management
- The first build may take longer due to dependency resolution
- Swift can import C libraries and frameworks
- On macOS, system frameworks are readily available
- The benchmark may use various packages from the Swift Package Index