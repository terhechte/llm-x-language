# Task: Function Call

Write a Zig function called `example` that takes a string slice and returns a string.

Example structure:
```zig
const std = @import("std");

pub fn example(allocator: std.mem.Allocator, input: []const u8) ![]const u8 {
    // Your implementation here
    // Note: In Zig, string operations often require an allocator
    return result;
}
```

The function should:
- Accept an allocator and a string slice (`[]const u8`) as parameters
- Process the input according to the task requirements
- Return an allocated string slice or an error
- Handle memory allocation properly