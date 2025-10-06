from pathlib import Path
from typing import Optional
from spawn_agent.terminal import execute_in_terminal, close_current_terminal

# Will be set by initialize() to the resolved claude command
_claude_command: str = "claude"


def set_claude_command(command: str) -> None:
    """Set the resolved claude command to use for spawning sessions"""
    global _claude_command
    _claude_command = command


def spawn_session(directory: str, driver: str = "claude", model: Optional[str] = None, background: bool = False) -> tuple[str, str]:
    """
    Spawn a new session in a terminal window

    Args:
        directory: The directory where the session should run
        driver: The CLI driver to use - "claude", "codex", or "crush" (default: "claude")
        model: Model name to use with "claude" driver (e.g., "qwen", "sonnet", "deepseek")
        background: If False, terminates the current session after spawning (default: False)

    Returns:
        Tuple of (status_message, unit_name) where unit_name is empty string on error
    """
    # Expand ~ in directory path
    directory = str(Path(directory).expanduser())

    # Validate driver
    valid_drivers = ["claude", "codex", "crush"]
    if driver not in valid_drivers:
        return (f"Error: Invalid driver '{driver}'. Must be one of: {', '.join(valid_drivers)}", "")

    # Validate model usage
    if model and driver != "claude":
        return (f"Error: model parameter can only be used with driver 'claude', not '{driver}'", "")

    # Construct the command based on driver and model
    if driver == "claude":
        if model:
            cmd_str = f"{_claude_command} --model {model}"
        else:
            cmd_str = _claude_command
    else:
        cmd_str = driver

    # Execute in terminal
    error_msg, unit_name = execute_in_terminal(cmd_str, directory)

    if error_msg:
        return (error_msg, "")

    session_desc = f"{driver}"
    if model:
        session_desc += f" (model: {model})"

    # If background is False, close the current terminal window
    if not background:
        close_current_terminal()

    return (f"Session '{session_desc}' spawned successfully in '{directory}' (Unit: {unit_name})", unit_name)
