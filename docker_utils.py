"""Docker integration utilities for the benchmark framework."""

import threading
import socket
from typing import Optional, Set
import logging


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


def build_docker_run_command(
    image: str,
    volume_mount: str,
    command: list,
    port: Optional[int] = None,
    network_mode: Optional[str] = None,
    container_name: Optional[str] = None,
    env_vars: Optional[dict] = None,
) -> list:
    """
    Build a docker run command with the given parameters.
    
    Args:
        image: Docker image name
        volume_mount: Volume mount in format "host_path:container_path"
        command: Command to run in the container
        port: Optional port to expose
        network_mode: Optional network mode (defaults to platform-specific)
        container_name: Optional container name
        env_vars: Optional environment variables
        
    Returns:
        List of command arguments for subprocess
    """
    cmd = ["docker", "run", "--rm"]
    
    # Add container name if provided
    if container_name:
        cmd.extend(["--name", container_name])
    
    # Add volume mount
    cmd.extend(["-v", volume_mount])
    
    # Add working directory
    cmd.extend(["-w", "/app"])
    
    # Add network mode
    if network_mode is None:
        network_mode = get_docker_network_mode()
    
    if network_mode == 'host':
        cmd.extend(["--network", "host"])
    elif port:
        # Only map ports in bridge mode
        cmd.extend(["-p", f"{port}:{port}"])
    
    # Add environment variables
    if env_vars:
        for key, value in env_vars.items():
            cmd.extend(["-e", f"{key}={value}"])
    
    # Add image
    cmd.append(image)
    
    # Add command
    cmd.extend(command)
    
    return cmd