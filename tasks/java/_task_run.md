# Task: HTTP Server

Create a simple HTTP server in Java.

The server should:
- Listen on the specified port
- Handle GET requests at "/"
- Return the expected response

Example structure using Spark Java:
```java
import static spark.Spark.*;

public class Main {
    public static void main(String[] args) {
        int port = 8080; // Or get from environment/arguments
        port(port);
        
        get("/", (req, res) -> {
            // Return your response
            return "Response content";
        });
    }
}
```

Note: You may also use Java's built-in HttpServer or other approaches for HTTP server implementation.