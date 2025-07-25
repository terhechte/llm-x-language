rockspec_format = "3.0"
package = "lua-container"
version = "1.0-1"
source = {
   url = "git+https://github.com/example/lua-container.git"
}
description = {
   summary = "Lua container for LLM benchmark execution",
   detailed = "A containerized Lua environment with necessary dependencies for executing LLM-generated code",
   homepage = "https://github.com/example/lua-container",
   license = "MIT"
}
dependencies = {
   "lua >= 5.1",
   "dkjson >= 2.5",
   "luasocket >= 3.0",
   "http >= 0.4"
}
build = {
   type = "builtin"
}