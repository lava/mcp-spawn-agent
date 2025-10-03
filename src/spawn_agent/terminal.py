import subprocess
from pathlib import Path
from spawn_agent.cgroup import execute_with_systemd_run

# Global terminal command - selected once at startup
TERMINAL_CMD = None


def find_available_terminal():
    """Find the first available terminal emulator on the system"""
    terminal_options = [
        ["gnome-terminal", "--working-directory", "{dir}", "--", "bash", "-c", "{cmd}; exec bash"],
        ["konsole", "--workdir", "{dir}", "-e", "bash", "-c", "{cmd}; exec bash"],
        ["xterm", "-e", "cd '{dir}' && {cmd}; exec bash"],
        ["x-terminal-emulator", "-e", "bash -c 'cd \"{dir}\" && {cmd}; exec bash'"]
    ]

    for terminal_template in terminal_options:
        try:
            subprocess.run([terminal_template[0], "--help"],
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL,
                         timeout=1)
            return terminal_template
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue

    return None


def initialize():
    """Initialize the terminal command at startup"""
    global TERMINAL_CMD
    TERMINAL_CMD = find_available_terminal()
    return TERMINAL_CMD is not None


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
        if TERMINAL_CMD is None:
            return ("Error: No suitable terminal emulator found. Please install gnome-terminal, konsole, xterm, or another terminal emulator.", "")

        # Build terminal command with placeholders filled
        terminal_cmd = []
        for part in TERMINAL_CMD:
            if "{dir}" in part:
                terminal_cmd.append(part.replace("{dir}", str(target_dir)))
            elif "{cmd}" in part:
                terminal_cmd.append(part.replace("{cmd}", command))
            else:
                terminal_cmd.append(part)

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
