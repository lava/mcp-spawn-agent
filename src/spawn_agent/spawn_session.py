from typing import Optional
from spawn_agent.terminal import execute_in_terminal


def spawn_session(directory: str, driver: str = "claude", model: Optional[str] = None) -> tuple[str, str]:
    """
    Spawn a new session in a terminal window

    Args:
        directory: The directory where the session should run
        driver: The CLI driver to use - "claude", "codex", or "crush" (default: "claude")
        model: Model name to use with "claude" driver (e.g., "qwen", "sonnet", "deepseek")

    Returns:
        Tuple of (status_message, unit_name) where unit_name is empty string on error
    """
    # Validate driver
    valid_drivers = ["claude", "codex", "crush"]
    if driver not in valid_drivers:
        return (f"Error: Invalid driver '{driver}'. Must be one of: {', '.join(valid_drivers)}", "")

    # Validate model usage
    if model and driver != "claude":
        return (f"Error: model parameter can only be used with driver 'claude', not '{driver}'", "")

    # Construct the command based on driver and model
    if driver == "claude" and model:
        cmd_str = f"ccr code --model {model}"
    else:
        cmd_str = driver

    # Execute in terminal
    error_msg, unit_name = execute_in_terminal(cmd_str, directory)

    if error_msg:
        return (error_msg, "")

    session_desc = f"{driver}"
    if model:
        session_desc += f" (model: {model})"

    return (f"Session '{session_desc}' spawned successfully in '{directory}' (Unit: {unit_name})", unit_name)
