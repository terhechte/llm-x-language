# Task: HTTP Server

Create a simple HTTP server in Zig.

The server should:
- Listen on the specified port
- Handle GET requests at "/"
- Return the expected response

Example structure:
```zig
const std = @import("std");
const net = std.net;

pub fn main() !void {
    const allocator = std.heap.page_allocator;
    
    // Parse port from environment or use default
    const port: u16 = 8080;
    
    // Create address
    const address = try net.Address.parseIp("127.0.0.1", port);
    
    // Create and bind server
    var server = net.StreamServer.init(.{});
    defer server.deinit();
    
    try server.listen(address);
    
    // Accept and handle connections
    while (true) {
        const connection = try server.accept();
        // Handle the connection
        // Read request, send response
    }
}
```

Note: Zig's standard library provides basic networking capabilities. For a full HTTP server, you might need to implement HTTP parsing or use a third-party library.