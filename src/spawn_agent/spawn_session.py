from spawn_agent.terminal import execute_in_terminal


def spawn_session(directory: str) -> tuple[str, str]:
    """
    Spawn a new Claude session in a terminal window

    Args:
        directory: The directory where the session should run

    Returns:
        Tuple of (status_message, unit_name) where unit_name is empty string on error
    """
    # Prepare the claude command string
    claude_cmd_str = "/home/benno/.claude/local/claude"

    # Execute in terminal
    error_msg, unit_name = execute_in_terminal(claude_cmd_str, directory)

    if error_msg:
        return (error_msg, "")

    return (f"Claude session spawned successfully in '{directory}' (Unit: {unit_name})", unit_name)
