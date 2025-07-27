FROM node:20-alpine

# Install pnpm
RUN corepack enable && corepack prepare pnpm@latest --activate

# Set working directory
WORKDIR /app

# Copy package files
COPY package.json pnpm-lock.yaml ./

# Install dependencies
RUN pnpm install --frozen-lockfile

# Copy TypeScript config
COPY tsconfig.json ./

# Default command (will be overridden by docker run)
CMD ["pnpm", "dev"]