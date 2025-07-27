#!/bin/bash

# Build all Docker images for the LLM benchmark framework

set -e  # Exit on error

echo "Building Docker images for LLM benchmark framework..."
echo "=============================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if docker-compose is available
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
else
    echo "Error: docker-compose is not installed. Please install docker-compose."
    exit 1
fi

# Build all images using docker-compose
echo "Building all language containers..."
$COMPOSE_CMD build --parallel

echo ""
echo "Build complete! The following images have been created:"
echo "------------------------------------------------------"
docker images | grep "llm-benchmark/" | awk '{print $1":"$2}'

echo ""
echo "To use Docker execution, set the environment variable:"
echo "  export LLM_BENCHMARK_USE_DOCKER=true"
echo ""
echo "Or pass use_docker=True when initializing language utils."