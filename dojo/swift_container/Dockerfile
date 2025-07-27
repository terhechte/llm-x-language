FROM swift:6.1.2

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libcurl4-openssl-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Package.swift
COPY Package.swift ./

# Create empty Sources directory to allow dependency resolution
RUN mkdir -p Sources && \
    echo "print(\"temp\")" > Sources/main.swift && \
    swift build && \
    rm -rf Sources

# Default command (will be overridden by docker run)
CMD ["swift", "run"]