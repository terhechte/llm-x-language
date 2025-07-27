FROM php:8.2-cli-bookworm

# Install additional PHP extensions if needed
RUN docker-php-ext-install sockets

# Set working directory
WORKDIR /app

# Default command (will be overridden by docker run)
CMD ["php", "main.php"]