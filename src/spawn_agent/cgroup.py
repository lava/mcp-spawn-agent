import os
import subprocess
from typing import Optional, NamedTuple


class SystemdUnit(NamedTuple):
    """Information about a systemd unit created by systemd-run"""
    unit_name: str
    # process: subprocess.Popen


def execute_with_systemd_run(command: list[str], unit_name: Optional[str] = None, working_directory: Optional[str] = None) -> SystemdUnit:
    """
    Execute a command using systemd-run --user --scope.
    
    Args:
        command: List of command arguments to execute
        unit_name: Optional name for the systemd unit. If None, generates a unique name.
        working_directory: Optional working directory for the command
        
    Returns:
        SystemdUnit containing unit name and process object
        
    Raises:
        OSError: If systemd-run execution fails
        subprocess.SubprocessError: If command execution fails
    """
    if unit_name is None:
        unit_name = f"spawn-agent-{os.getpid()}-{os.urandom(4).hex()}"
    
    # Build systemd-run command
    systemd_cmd = [
        "systemd-run",
        "--user",
        "--scope",
        "--unit", unit_name,
        "--description", f"Spawned agent: {' '.join(command[:3])}...",
        "--collect",  # Auto-cleanup when done
    ]
    
    # Add working directory if specified
    if working_directory:
        systemd_cmd.extend(["--working-directory", working_directory])
    
    # Add the actual command
    systemd_cmd.extend(["--"])
    systemd_cmd.extend(command)
    
    try:
        # Execute with systemd-run
        process = subprocess.Popen(
            systemd_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        process.wait()
        
        return SystemdUnit(unit_name=unit_name)
        
    except Exception as e:
        raise OSError(f"Failed to execute command with systemd-run: {e}")


def stop_systemd_unit(unit_name: str) -> None:
    """
    Stop a systemd user unit.
    
    Args:
        unit_name: Name of the systemd unit to stop
        
    Raises:
        OSError: If stop operation fails
    """
    try:
        subprocess.run(
            ["systemctl", "--user", "stop", unit_name],
            check=True,
            capture_output=True,
            text=True
        )
    except subprocess.CalledProcessError as e:
        raise OSError(f"Failed to stop systemd unit {unit_name}: {e.stderr}")


def kill_systemd_unit(unit_name: str, signal_name: str = "SIGKILL") -> None:
    """
    Send a signal to all processes in a systemd user unit.
    
    Args:
        unit_name: Name of the systemd unit
        signal_name: Signal to send (default: SIGKILL)
        
    Raises:
        OSError: If kill operation fails
    """
    try:
        subprocess.run(
            ["systemctl", "--user", "kill", f"--signal={signal_name}", unit_name],
            check=True,
            capture_output=True,
            text=True
        )
    except subprocess.CalledProcessError as e:
        raise OSError(f"Failed to kill systemd unit {unit_name}: {e.stderr}")


def cleanup_systemd_unit(unit_name: str) -> None:
    """
    Clean up a systemd user unit by stopping it and resetting its state.
    
    Args:
        unit_name: Name of the systemd unit to clean up
        
    Raises:
        OSError: If cleanup fails
    """
    try:
        # Stop the unit (if running)
        subprocess.run(
            ["systemctl", "--user", "stop", unit_name],
            capture_output=True,
            text=True
        )
        
        # Reset any failure state
        subprocess.run(
            ["systemctl", "--user", "reset-failed", unit_name],
            capture_output=True,
            text=True
        )
        
    except Exception as e:
        raise OSError(f"Failed to cleanup systemd unit {unit_name}: {e}")


def list_spawned_units() -> list[str]:
    """
    List all running spawn-agent systemd units.
    
    Returns:
        List of unit names that are spawn-agent related
        
    Raises:
        OSError: If listing units fails
    """
    try:
        result = subprocess.run(
            ["systemctl", "--user", "list-units", "--plain", "--no-legend", "spawn-agent-*"],
            check=True,
            capture_output=True,
            text=True
        )
        
        units = []
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                # Extract unit name (first column)
                unit_name = line.split()[0]
                if unit_name.startswith('spawn-agent-'):
                    units.append(unit_name)
        
        return units
        
    except subprocess.CalledProcessError as e:
        raise OSError(f"Failed to list systemd units: {e.stderr}")
