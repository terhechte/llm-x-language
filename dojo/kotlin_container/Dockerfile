FROM openjdk:17-slim

# Install required dependencies
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy gradle files
COPY gradlew gradlew.bat ./
COPY gradle ./gradle
COPY build.gradle.kts settings.gradle.kts gradle.properties ./

# Make gradlew executable
RUN chmod +x gradlew

# Download dependencies
RUN ./gradlew dependencies --no-daemon || true

# Default command - will be overridden by docker run
# Note: Building and running must be done in separate steps
CMD ["./gradlew", "nativeBinaries", "--console=plain"]