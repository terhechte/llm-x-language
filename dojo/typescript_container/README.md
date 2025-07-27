# TypeScript Container

This container provides a TypeScript/Node.js environment for executing LLM-generated TypeScript code.

## Prerequisites

- **Node.js**: Version 18 or higher
- **pnpm**: Fast, disk space efficient package manager

## Installation

### Installing Node.js

#### macOS
```bash
# Using Homebrew
brew install node

# Or using Node Version Manager (nvm)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install node
```

#### Linux
```bash
# Using NodeSource repository (Ubuntu/Debian)
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt-get install -y nodejs

# Using nvm (recommended)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install node
```

#### Windows
Download the installer from https://nodejs.org/ or use Windows Package Manager:
```powershell
winget install OpenJS.NodeJS
```

### Installing pnpm

```bash
# Using npm (comes with Node.js)
npm install -g pnpm

# Or using Homebrew (macOS)
brew install pnpm

# Or using standalone script
curl -fsSL https://get.pnpm.io/install.sh | sh -
```

## Dependencies

Dependencies are managed through `package.json`:

### Runtime Dependencies
- **axios**: Promise-based HTTP client
- **date-fns**: Modern JavaScript date utility library
- **express**: Fast, minimalist web framework
- **zod**: TypeScript-first schema validation

### Development Dependencies
- **typescript**: TypeScript language
- **tsx**: TypeScript execute - Node.js enhanced with TypeScript support
- **@types/node**: TypeScript definitions for Node.js
- **@types/express**: TypeScript definitions for Express
- **ts-node**: TypeScript execution engine for Node.js

## Usage

The benchmark framework will:
1. Write TypeScript code to `src/index.ts`
2. Run type checking using `tsc --noEmit`
3. Execute the code using `tsx` in development mode
4. Optionally build to JavaScript using `tsc`

## Commands Used by Benchmark

- **Install dependencies**: `pnpm install`
- **Type check**: `pnpm run typecheck` (runs `tsc --noEmit`)
- **Run development**: `pnpm dev` (runs `tsx src/index.ts`)
- **Build**: `pnpm run build` (compiles TypeScript to JavaScript)
- **Run production**: `pnpm start` (runs compiled JavaScript)

## Project Structure

```
typescript_container/
├── package.json      # Project configuration and dependencies
├── pnpm-lock.yaml   # Locked dependency versions
├── tsconfig.json    # TypeScript configuration
├── src/
│   └── index.ts     # Main source file (replaced during benchmark)
└── dist/            # Compiled JavaScript output (after build)
```

## Notes

- The project is configured as an ES module (`"type": "module"` in package.json)
- TypeScript is configured with strict type checking
- `tsx` allows running TypeScript directly without compilation during development
- The benchmark may import various npm packages
- First run may take longer due to dependency installation