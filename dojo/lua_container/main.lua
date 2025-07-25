
local json = require("dkjson")

function hello()
    local data = {message = "Hello from Lua container!", status = "success"}
    return json.encode(data)
end

print(hello())
