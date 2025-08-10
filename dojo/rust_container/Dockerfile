FROM rust:latest

# Install build dependencies
RUN apt-get update && apt-get install -y \
    pkg-config \
    libssl-dev \
    gcc \
    libc-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Cargo.toml only (skip Cargo.lock to avoid version conflicts)
COPY Cargo.toml ./

# Create necessary directories
RUN mkdir -p src target

# Pre-build dependencies with a dummy main.rs
# Use debug mode for faster initial builds
# This will generate a new Cargo.lock compatible with this Rust version
RUN echo "fn main() {}" > src/main.rs && \
    cargo build && \
    rm -rf src/main.rs

# Default command (will be overridden by docker run)
CMD ["cargo", "run", "-q"]