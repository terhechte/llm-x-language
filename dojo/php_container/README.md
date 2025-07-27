# PHP Container

This container provides a PHP environment for executing LLM-generated PHP code.

## Prerequisites

- **PHP**: Version 7.4 or higher

## Installation

### Installing PHP

#### macOS
```bash
# Using Homebrew
brew install php

# Or use MacPorts
sudo port install php84
```

#### Linux
```bash
# Ubuntu/Debian
sudo apt-get install php php-cli

# Fedora
sudo dnf install php php-cli

# Arch Linux
sudo pacman -S php
```

#### Windows
Download the installer from https://windows.php.net/download/

## Dependencies

This container runs PHP in its simplest form without any external dependencies or package managers. The PHP standard library provides all necessary functionality.

## Usage

The benchmark framework will:
1. Write PHP code to `main.php`
2. Validate syntax using `php -l`
3. Execute the code using `php main.php`

## Commands Used by Benchmark

- **Validate**: `php -l main.php` (syntax check)
- **Run**: `php main.php`

## Notes

- No composer or other package managers are used
- All functionality relies on PHP's built-in functions and classes
- The benchmark may use various PHP standard library features
- Error reporting is typically enabled for debugging