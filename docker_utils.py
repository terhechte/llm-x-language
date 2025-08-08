"""Docker integration utilities for the benchmark framework.

This module provides helpers to run containers in a way that avoids
shared volume mounts between concurrent tests. Instead of `docker run` with
`-v`, we create a container, copy code into it, and then start it. This
prevents parallel runs from overwriting each other's files.
"""

import threading
import socket
from typing import Optional, Set, Dict, List
import logging
import subprocess


class PortManager:
    """
    Thread-safe port allocation manager for Docker containers.
    Ensures unique port assignments for concurrent HTTP server tests.
    """
    
    def __init__(self, base_port: int = 8000, max_port: int = 9000):
        """
        Initialize the port manager.
        
        Args:
            base_port: Starting port number (default: 8000)
            max_port: Maximum port number to allocate (default: 9000)
        """
        self.base_port = base_port
        self.max_port = max_port
        self.allocated_ports: Set[int] = set()
        self.lock = threading.Lock()
    
    def allocate_port(self) -> Optional[int]:
        """
        Allocate an available port.
        
        Returns:
            An available port number, or None if no ports available
        """
        with self.lock:
            for port in range(self.base_port, self.max_port):
                if port not in self.allocated_ports and self._is_port_available(port):
                    self.allocated_ports.add(port)
                    logging.debug(f"Allocated port {port}")
                    return port
            return None
    
    def release_port(self, port: int):
        """
        Release a previously allocated port.
        
        Args:
            port: Port number to release
        """
        with self.lock:
            if port in self.allocated_ports:
                self.allocated_ports.remove(port)
                logging.debug(f"Released port {port}")
    
    def _is_port_available(self, port: int) -> bool:
        """
        Check if a port is available on the host.
        
        Args:
            port: Port number to check
            
        Returns:
            True if port is available, False otherwise
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind(('', port))
                return True
        except OSError:
            return False
    
    def get_allocated_count(self) -> int:
        """Get the number of currently allocated ports."""
        with self.lock:
            return len(self.allocated_ports)


# Global port manager instance
port_manager = PortManager()


def get_docker_network_mode() -> str:
    """
    Get the appropriate Docker network mode based on the platform.
    
    Returns:
        'host' for Linux, 'bridge' for macOS/Windows
    """
    import platform
    system = platform.system().lower()
    
    # On Linux, we can use host networking for better performance
    # On macOS/Windows, Docker Desktop doesn't support host networking
    if system == 'linux':
        return 'host'
    else:
        return 'bridge'


def build_docker_create_command(
    image: str,
    command: List[str],
    *,
    port: Optional[int] = None,
    network_mode: Optional[str] = None,
    container_name: Optional[str] = None,
    env_vars: Optional[Dict[str, str]] = None,
) -> List[str]:
    """Build a `docker create` command with the given parameters.

    We use this instead of `docker run -v` to avoid mounting shared host
    directories across parallel runs. Files are copied in after creation.
    """
    # Note: `docker create` does not support --rm; handle cleanup manually.
    cmd = ["docker", "create"]

    if container_name:
        cmd.extend(["--name", container_name])

    # Working directory is /app in all dojo images
    cmd.extend(["-w", "/app"])

    # Determine network mode
    if network_mode is None:
        network_mode = get_docker_network_mode()

    if network_mode == "host":
        cmd.extend(["--network", "host"])
    elif port:
        # Only map ports when using bridge mode
        cmd.extend(["-p", f"{port}:{port}"])

    # Environment variables
    if env_vars:
        for k, v in env_vars.items():
            cmd.extend(["-e", f"{k}={v}"])

    # Image and command
    cmd.append(image)
    cmd.extend(command)

    return cmd


def docker_cp(src: str, dst: str) -> subprocess.CompletedProcess:
    """Copy a file or directory into a container using `docker cp`.

    `dst` is of the form `container_id:/path/in/container`.
    """
    return subprocess.run(["docker", "cp", src, dst], capture_output=True, text=True)


def docker_create(image: str, command: List[str], *, port: Optional[int] = None,
                  network_mode: Optional[str] = None,
                  container_name: Optional[str] = None,
                  env_vars: Optional[Dict[str, str]] = None) -> str:
    """Create a container and return its container id."""
    create_cmd = build_docker_create_command(
        image=image,
        command=command,
        port=port,
        network_mode=network_mode,
        container_name=container_name,
        env_vars=env_vars,
    )
    result = subprocess.run(create_cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        logging.error("Failed to create container: %s", result.stderr)
        raise subprocess.SubprocessError(result.stderr.strip())
    return result.stdout.strip()


def docker_start_attach(container_id: str, *, timeout: Optional[int] = None) -> subprocess.CompletedProcess:
    """Start the container and attach to its output until it exits."""
    return subprocess.run(["docker", "start", "-a", container_id], capture_output=True, text=True, timeout=timeout)


def docker_stop_rm(container_id: str, *, force: bool = False) -> None:
    """Stop and remove a container, ignoring errors."""
    try:
        subprocess.run(["docker", "stop", container_id], capture_output=True, text=True, check=False)
    finally:
        if force:
            subprocess.run(["docker", "rm", "-f", container_id], capture_output=True, text=True, check=False)
        else:
            subprocess.run(["docker", "rm", container_id], capture_output=True, text=True, check=False)
