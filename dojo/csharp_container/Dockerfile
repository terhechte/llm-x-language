FROM mcr.microsoft.com/dotnet/sdk:8.0

# Install build dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project file
COPY csharp_container.csproj ./

# Restore dependencies
RUN dotnet restore

# Create necessary directories
RUN mkdir -p bin obj

# Pre-build with a dummy Program.cs to cache dependencies
RUN echo "Console.WriteLine(\"temp\");" > Program.cs && \
    dotnet build && \
    rm -f Program.cs

# Default command (will be overridden by docker run)
CMD ["dotnet", "run"]