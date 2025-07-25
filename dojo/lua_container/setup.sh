#!/bin/bash
# Setup script to install Lua dependencies

# Check if luarocks is installed
if ! command -v luarocks &> /dev/null
then
    echo "luarocks is not installed. Please install it first."
    exit 1
fi

# Install dependencies
echo "Installing Lua dependencies..."
luarocks install dkjson --local
luarocks install luasocket --local
luarocks install http --local

echo "Lua dependencies installed successfully!"