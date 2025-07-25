#!/bin/bash
# Run script that sets up Lua environment with luarocks paths

# Get luarocks paths if luarocks is available
if command -v luarocks &> /dev/null; then
    eval $(luarocks path)
fi

# Run the main.lua file
lua main.lua