FROM golang:1.24.5-alpine

# Install additional tools
RUN apk add --no-cache git && \
    go install golang.org/x/tools/cmd/goimports@latest

# Set working directory
WORKDIR /app

# Copy go.mod
COPY go.mod ./

# Download dependencies if any
RUN go mod download || true

# Default command (will be overridden by docker run)
CMD ["go", "run", "main.go"]