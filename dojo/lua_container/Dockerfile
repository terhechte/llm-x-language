FROM alpine:3.19

# Install Lua and LuaRocks
RUN apk add --no-cache \
    lua5.4 \
    lua5.4-dev \
    luarocks5.4 \
    gcc \
    musl-dev \
    openssl-dev \
    curl

# Create symlinks for easier access
RUN ln -s /usr/bin/lua5.4 /usr/bin/lua && \
    ln -s /usr/bin/luac5.4 /usr/bin/luac && \
    ln -s /usr/bin/luarocks-5.4 /usr/bin/luarocks

# Set working directory
WORKDIR /app

# Copy setup script and rockspec
COPY setup.sh lua-container-1.0-1.rockspec ./
COPY run.sh ./

# Make scripts executable
RUN chmod +x setup.sh run.sh

# Install dependencies
RUN ./setup.sh || true

# Default command (will be overridden by docker run)
CMD ["./run.sh"]