FROM openjdk:17-slim

# Install required dependencies including GCC for Kotlin Native
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    gcc \
    libc-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy gradle files
COPY gradlew gradlew.bat ./
COPY gradle ./gradle
COPY build.gradle.kts settings.gradle.kts gradle.properties ./

# Make gradlew executable
RUN chmod +x gradlew

# Set Kotlin Native target to Linux
ENV KONAN_DATA_DIR=/tmp/konan

# Download dependencies and pre-build for Linux target
RUN ./gradlew dependencies --no-daemon || true

# Pre-build empty JAR to speed up execution
RUN mkdir -p src/main/kotlin && \
    echo 'fun main() { println("Ready") }' > src/main/kotlin/Main.kt && \
    ./gradlew jar --no-daemon

# Default command - will be overridden by docker run
CMD ["/usr/local/openjdk-17/bin/java", "-jar", "build/libs/kotlin_container.jar"]