const std = @import("std");

pub fn build(b: *std.Build) void {
    // Standard target and optimization options
    const target = b.standardTargetOptions(.{});
    const optimize = b.standardOptimizeOption(.{});

    // Create executable
    const exe = b.addExecutable(.{
        .name = "main",
        .root_source_file = b.path("src/main.zig"),
        .target = target,
        .optimize = optimize,
    });

    // Note: To add httpz dependency, uncomment the following:
    // const httpz_dep = b.dependency("httpz", .{
    //     .target = target,
    //     .optimize = optimize,
    // });
    // exe.root_module.addImport("httpz", httpz_dep.module("httpz"));

    // Install the executable
    b.installArtifact(exe);

    // Create run command
    const run_cmd = b.addRunArtifact(exe);
    run_cmd.step.dependOn(b.getInstallStep());

    // Add run step
    const run_step = b.step("run", "Run the app");
    run_step.dependOn(&run_cmd.step);
}