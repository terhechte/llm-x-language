# Rust Container

This container provides a Rust environment for executing LLM-generated Rust code.

## Prerequisites

- **Rust**: Latest stable version
- **Cargo**: Rust's build system and package manager (included with Rust)

## Installation

### Installing Rust

The recommended way to install Rust is through rustup, the official Rust toolchain installer.

#### All Platforms
```bash
# Install rustup
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Follow the on-screen instructions, then reload your shell configuration
source $HOME/.cargo/env

# Verify installation
rustc --version
cargo --version
```

#### Alternative Methods

**macOS (using Homebrew)**
```bash
brew install rust
```

**Linux Package Managers**
```bash
# Ubuntu/Debian (not recommended - often outdated)
sudo apt-get install rust cargo

# Fedora
sudo dnf install rust cargo

# Arch Linux
sudo pacman -S rust
```

## Dependencies

Dependencies are managed through `Cargo.toml`. The specific dependencies will vary based on the benchmark tasks but are automatically downloaded and compiled by Cargo.

## Usage

The benchmark framework will:
1. Write Rust code to `src/main.rs`
2. Validate the code using `cargo check`
3. Run the code using `cargo run`
4. Optionally build a release binary using `cargo build --release`

## Commands Used by Benchmark

- **Validate**: `cargo check --message-format=json`
- **Run**: `cargo run -q` (quiet mode, suppresses Cargo output)
- **Build**: `cargo build`
- **Build Release**: `cargo build --release`

## Project Structure

```
rust_container/
├── Cargo.toml       # Project manifest and dependencies
├── Cargo.lock       # Locked dependency versions
└── src/
    └── main.rs      # Main source file (replaced during benchmark)
```

## Notes

- Cargo automatically downloads and compiles dependencies
- The first build may take longer due to dependency compilation
- Subsequent runs use cached compiled dependencies
- The benchmark may use various crates from crates.io
- Error messages from rustc are generally very helpful for debugging