# Kotlin Container

This container provides a Kotlin Native environment for executing LLM-generated Kotlin code.

## Prerequisites

- **Kotlin Native**: Kotlin/Native compiler
- **Java JDK**: Version 8 or higher (required for Gradle)

## Installation

### Installing Java JDK

#### macOS
```bash
# Using Homebrew
brew install openjdk

# Or download from https://adoptium.net/
```

#### Linux
```bash
# Ubuntu/Debian
sudo apt-get install default-jdk

# Fedora
sudo dnf install java-latest-openjdk
```

#### Windows
Download the installer from https://adoptium.net/

### Installing Kotlin Native

The Kotlin Native compiler is managed by Gradle and will be automatically downloaded when building the project. No separate installation is required.

## Dependencies

Dependencies are managed through `build.gradle.kts`:
- **kotlinx-serialization-json**: JSON serialization support
- **kotlinx-datetime**: Date and time utilities
- **ktor-client**: HTTP client functionality
- **ktor-server**: HTTP server functionality

## Build System

This project uses Gradle with the Kotlin/Native plugin. The Gradle wrapper (`gradlew` or `gradlew.bat`) is included in the project.

## Usage

The benchmark framework will:
1. Write Kotlin code to `src/nativeMain/kotlin/main.kt`
2. Build the native executable using Gradle
3. Run the compiled executable

## Commands Used by Benchmark

- **Build**: `./gradlew nativeBinaries --console=plain` (or `gradlew.bat` on Windows)
- **Run**: `./build/bin/native/releaseExecutable/main.kexe`

## Project Structure

```
kotlin_container/
├── build.gradle.kts      # Build configuration
├── settings.gradle.kts   # Project settings
├── gradle.properties     # Gradle properties
├── gradlew              # Gradle wrapper (Unix)
├── gradlew.bat          # Gradle wrapper (Windows)
└── src/
    └── nativeMain/
        └── kotlin/
            └── main.kt  # Main source file (replaced during benchmark)
```

## Notes

- The project is configured to build native executables
- No JVM is required at runtime (only for building)
- The Gradle wrapper ensures consistent builds across different environments