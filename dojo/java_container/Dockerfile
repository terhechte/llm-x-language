FROM openjdk:17-slim

# Install build tools and dependencies
RUN apt-get update && apt-get install -y \
    maven \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create project structure
RUN mkdir -p src/main/java

# Copy pom.xml for Maven dependencies
COPY pom.xml ./

# Download dependencies
RUN mvn dependency:go-offline

# Pre-compile with dummy file to cache dependencies
RUN echo 'public class Main { public static void main(String[] args) { System.out.println("Hello World"); } }' > src/main/java/Main.java && \
    mvn compile && \
    rm -rf src/main/java/Main.java target

# Default command
CMD ["java", "-cp", "target/classes", "Main"]