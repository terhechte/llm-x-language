# Task: HTTP Server

Create a simple HTTP server in C++.

The server should:
- Listen on the specified port
- Handle GET requests at "/"
- Return the expected response

Example structure using a simple approach:
```cpp
#include <iostream>
#include <string>
#include <sstream>
#include <sys/socket.h>
#include <netinet/in.h>
#include <unistd.h>

int main() {
    int port = 8080; // Or get from environment/arguments
    
    // Create socket
    int server_fd = socket(AF_INET, SOCK_STREAM, 0);
    
    // Bind and listen
    struct sockaddr_in address;
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(port);
    
    bind(server_fd, (struct sockaddr*)&address, sizeof(address));
    listen(server_fd, 3);
    
    // Accept connections and handle requests
    // ...
    
    return 0;
}
```

Note: You may also use libraries like Boost.Beast or cpp-httplib for easier HTTP server implementation.