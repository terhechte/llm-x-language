FROM gcc:latest

# Install build dependencies
RUN apt-get update && apt-get install -y \
    cmake \
    make \
    g++ \
    curl \
    libcurl4-openssl-dev \
    nlohmann-json3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create project structure
RUN mkdir -p src

# Create CMakeLists.txt
COPY CMakeLists.txt ./

# Pre-compile with dummy file to cache compilation environment
RUN echo '#include <iostream>\nint main() { std::cout << "Hello World" << std::endl; return 0; }' > src/main.cpp && \
    cmake . && \
    make && \
    rm -f src/main.cpp CMakeCache.txt Makefile cmake_install.cmake CMakeFiles -rf

# Default command
CMD ["./main"]