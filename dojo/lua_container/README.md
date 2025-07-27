# Lua Container

This container provides a Lua environment for executing LLM-generated Lua code.

## Prerequisites

- **Lua**: Version 5.1 or higher
- **LuaRocks**: Lua package manager (optional but recommended)
- **Lua compiler (luac)**: Usually included with Lua installation

## Installation

### Installing Lua

#### macOS
```bash
# Using Homebrew
brew install lua

# This usually includes lua, luac, and luarocks
```

#### Linux
```bash
# Ubuntu/Debian
sudo apt-get install lua5.4 lua5.4-dev

# Fedora
sudo dnf install lua lua-devel

# Arch Linux
sudo pacman -S lua
```

#### Windows
Download LuaBinaries from http://luabinaries.sourceforge.net/ or use:
```powershell
# Using Chocolatey
choco install lua
```

### Installing LuaRocks

#### macOS
```bash
brew install luarocks
```

#### Linux
```bash
# Ubuntu/Debian
sudo apt-get install luarocks

# From source (universal method)
wget https://luarocks.org/releases/luarocks-3.9.2.tar.gz
tar zxpf luarocks-3.9.2.tar.gz
cd luarocks-3.9.2
./configure && make && sudo make install
```

## Dependencies

The following Lua libraries are installed via LuaRocks:
- **dkjson**: JSON encoding/decoding library
- **luasocket**: Networking support (TCP/UDP sockets)
- **http**: HTTP client functionality built on luasocket

## Setup

To install dependencies locally:

```bash
# Using the provided setup script
./setup.sh

# Or manually with luarocks
luarocks install dkjson --local
luarocks install luasocket --local
luarocks install http --local
```

The setup script will install packages locally to avoid requiring system-wide permissions.

## Usage

The benchmark framework will:
1. Write Lua code to `main.lua`
2. Validate syntax using `luac -p main.lua`
3. Execute using the wrapper script: `./run.sh`
4. The wrapper script sets up LuaRocks paths and runs `lua main.lua`

## Commands Used by Benchmark

- **Validate**: `luac -p main.lua` (syntax check)
- **Run**: `./run.sh` (which internally runs `lua main.lua` with proper paths)
- **Direct run**: `lua main.lua` (if LuaRocks packages are globally installed)

## Project Structure

```
lua_container/
├── README.md                      # This file
├── lua-container-1.0-1.rockspec  # LuaRocks package specification
├── setup.sh                       # Dependency installation script
├── run.sh                         # Execution wrapper script
└── main.lua                       # Main source file (replaced during benchmark)
```

## Notes

- The `run.sh` script configures LUA_PATH and LUA_CPATH for local LuaRocks packages
- Lua is lightweight and starts very quickly
- The benchmark may use various Lua standard library modules
- LuaRocks is optional if dependencies are installed system-wide
- The container supports both Lua 5.1+ and LuaJIT