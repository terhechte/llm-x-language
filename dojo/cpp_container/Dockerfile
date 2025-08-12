FROM gcc:latest

# Install build dependencies
RUN apt-get update && apt-get install -y \
    cmake \
    make \
    g++ \
    curl \
    libcurl4-openssl-dev \
    nlohmann-json3-dev \
    libboost-date-time-dev \
    && rm -rf /var/lib/apt/lists/*

# Install cpp-httplib (header-only HTTP server library)
RUN curl -L https://github.com/yhirose/cpp-httplib/archive/refs/tags/v0.14.3.tar.gz | tar xz -C /usr/include --strip-components=1 cpp-httplib-0.14.3/httplib.h

WORKDIR /app

# Create project structure
RUN mkdir -p src

# Create CMakeLists.txt
COPY CMakeLists.txt ./

# Pre-compile with dummy file to cache compilation environment
RUN echo '#include <iostream>\nint main() { std::cout << "Hello World" << std::endl; return 0; }' > src/main.cpp && \
    cmake . && \
    make && \
    rm -f src/main.cpp main CMakeCache.txt Makefile cmake_install.cmake CMakeFiles -rf

# Default command
CMD ["./main"]