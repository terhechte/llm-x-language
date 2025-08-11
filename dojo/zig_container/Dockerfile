FROM debian:bookworm-slim

# Install Zig and dependencies
RUN apt-get update && apt-get install -y \
    curl \
    xz-utils \
    && rm -rf /var/lib/apt/lists/*

# Download and install Zig
ENV ZIG_VERSION=0.13.0
RUN curl -L https://ziglang.org/download/${ZIG_VERSION}/zig-linux-$(uname -m | sed 's/aarch64/aarch64/;s/x86_64/x86_64/')-${ZIG_VERSION}.tar.xz | tar -xJ -C /opt && \
    ln -s /opt/zig-linux-$(uname -m | sed 's/aarch64/aarch64/;s/x86_64/x86_64/')-${ZIG_VERSION}/zig /usr/local/bin/zig

WORKDIR /app

# Create project structure
RUN mkdir -p src

# Copy build files
COPY build.zig ./
COPY build.zig.zon ./

# Pre-compile with dummy file to test setup
RUN printf 'const std = @import("std");\npub fn main() void {\n    std.debug.print("Hello World\\n", .{});\n}\n' > src/main.zig && \
    zig build-exe src/main.zig -femit-bin=main && \
    rm -f src/main.zig main

# Default command
CMD ["./main"]