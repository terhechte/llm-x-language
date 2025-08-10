# Task: HTTP Server

Create a simple HTTP server in C# using ASP.NET Core minimal APIs.

The server should:
- Listen on the specified port
- Handle GET requests at the root path "/"
- Return the expected response

Example structure:
```csharp
var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();

app.MapGet("/", () => "Response text");

app.Run("http://localhost:PORT");
```

Replace PORT with the appropriate port number from the task.