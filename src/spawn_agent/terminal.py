import os
import signal
import subprocess
from pathlib import Path
from typing import Protocol, Optional
from spawn_agent.cgroup import execute_with_systemd_run


class Terminal(Protocol):
    """Protocol for terminal emulator implementations"""

    @staticmethod
    def detect() -> bool:
        """Check if this terminal emulator is available"""
        ...

    @staticmethod
    def spawn(command: str, directory: str) -> list[str]:
        """
        Build the command to spawn a new terminal window.

        Returns a list of command arguments to execute.
        """
        ...

    @staticmethod
    def close_current() -> bool:
        """
        Close the current terminal window.

        Returns True if successfully closed, False otherwise.
        """
        ...


class GnomeTerminal:
    """Implementation for gnome-terminal"""

    @staticmethod
    def detect() -> bool:
        """Check if gnome-terminal is available"""
        try:
            subprocess.run(
                ["gnome-terminal", "--help"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=1
            )
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    @staticmethod
    def spawn(command: str, directory: str) -> list[str]:
        """Build command to spawn a new gnome-terminal window"""
        return [
            "gnome-terminal",
            "--working-directory", directory,
            "--", "bash", "-c", f"{command}; exec bash"
        ]

    @staticmethod
    def close_current() -> bool:
        """Close the current gnome-terminal tab/window by killing the shell"""
        try:
            # Walk up the process tree to find the bash shell started by gnome-terminal
            # Process tree: gnome-terminal-server -> bash -> claude -> ... -> python (MCP server)
            current_pid = os.getpid()

            # Walk up to find bash process
            for _ in range(10):  # Limit search depth
                # Get parent PID and command
                result = subprocess.run(
                    ['ps', '-o', 'ppid=,comm=', '-p', str(current_pid)],
                    capture_output=True,
                    text=True,
                    timeout=1
                )
                if result.returncode != 0:
                    return False

                parts = result.stdout.strip().split(None, 1)
                if len(parts) < 2:
                    return False

                parent_pid = int(parts[0])
                comm = parts[1]

                # If we found bash, kill it with SIGHUP
                if comm in ('bash', 'sh', 'zsh', 'fish'):
                    os.kill(parent_pid, signal.SIGHUP)
                    return True

                # Move up to parent
                current_pid = parent_pid

            return False
        except (subprocess.TimeoutExpired, FileNotFoundError, ProcessLookupError, ValueError):
            return False


# Registry of terminal implementations - ordered by preference
TERMINAL_IMPLEMENTATIONS: list[type[Terminal]] = [
    GnomeTerminal,
    # Add more terminal implementations here
]

# Global terminal implementation - selected once at startup
TERMINAL_IMPL: Optional[type[Terminal]] = None


def initialize() -> bool:
    """Initialize the terminal implementation at startup"""
    global TERMINAL_IMPL

    for terminal_class in TERMINAL_IMPLEMENTATIONS:
        if terminal_class.detect():
            TERMINAL_IMPL = terminal_class
            return True

    return False


def execute_in_terminal(command: str, directory: str) -> tuple[str, str]:
    """
    Execute a command in a new terminal window using systemd-run

    Args:
        command: The command to execute
        directory: The working directory for the command

    Returns:
        Tuple of (status_message, unit_name) where unit_name is empty string on error
    """
    try:
        # Resolve the target directory
        target_dir = Path(directory).resolve()
        if not target_dir.exists():
            return (f"Error: Directory '{directory}' does not exist", "")

        # Check if terminal is available
        if TERMINAL_IMPL is None:
            return ("Error: No suitable terminal emulator found. Please install gnome-terminal or another supported terminal emulator.", "")

        # Build terminal command using the implementation
        terminal_cmd = TERMINAL_IMPL.spawn(command, str(target_dir))

        # Execute the terminal emulator using systemd-run
        try:
            systemd_unit = execute_with_systemd_run(
                terminal_cmd,
                working_directory=str(target_dir)
            )
            unit_name = systemd_unit.unit_name
        except OSError as e:
            return (f"Error: Failed to execute terminal with systemd-run: {e}", "")

        return ("", unit_name)

    except Exception as e:
        return (f"Error executing in terminal: {e}", "")


def close_current_terminal() -> bool:
    """
    Close the current terminal window.

    Returns True if successfully closed, False otherwise.
    """
    if TERMINAL_IMPL is None:
        return False

    return TERMINAL_IMPL.close_current()
