Zig 0.13 standard library is available (`@import("std")`).

The standard library includes:
- HTTP client (`std.http.Client`) - for making HTTP requests
- HTTP server (`std.http.Server`) - for creating HTTP servers  
- Networking (`std.net`) - TCP/UDP sockets, addresses
- JSON parsing (`std.json`) - parse and stringify JSON
- Time functions (`std.time`) - timestamps, sleep, Timer
- Memory management (`std.mem`)
- I/O operations (`std.io`)
- File system (`std.fs`)
- Data structures (`std.ArrayList`, `std.HashMap`, etc.)
- Cryptography (`std.crypto`)
- Threading (`std.Thread`)

For more advanced HTTP server capabilities, httpz (github.com/karlseguin/http.zig) can be added as a dependency.

NO OTHER PACKAGES ARE AVAILABLE BY DEFAULT.

Don't show the output of the required code, just the code in markdown ticks (```{{lang}}).