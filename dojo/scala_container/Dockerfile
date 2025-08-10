FROM openjdk:17-slim

# Install SBT
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    && echo "deb https://repo.scala-sbt.org/scalasbt/debian all main" | tee /etc/apt/sources.list.d/sbt.list \
    && echo "deb https://repo.scala-sbt.org/scalasbt/debian /" | tee /etc/apt/sources.list.d/sbt_old.list \
    && curl -sL "https://keyserver.ubuntu.com/pks/lookup?op=get&search=0x2EE0EA64E40A89B84B2DF73499E82A75642AC823" | apt-key add \
    && apt-get update \
    && apt-get install -y sbt \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create project structure
RUN mkdir -p src/main/scala project

# Copy build.sbt
COPY build.sbt ./

# Copy project plugins
COPY project/build.properties project/
COPY project/plugins.sbt project/

# Download dependencies
RUN sbt update

# Pre-compile with dummy file to cache dependencies
RUN echo 'object Main { def main(args: Array[String]): Unit = println("Hello World") }' > src/main/scala/Main.scala && \
    sbt compile && \
    rm -rf src/main/scala/Main.scala target

# Default command
CMD ["sbt", "run"]