from pathlib import Path
from spawn_agent.terminal import execute_in_terminal

# Will be set by server.py to the resolved claude command
_claude_command: str = "claude"


def set_claude_command(command: str) -> None:
    """Set the resolved claude command to use for spawning subagents"""
    global _claude_command
    _claude_command = command


def spawn_subagent(agent_name: str, directory: str, task: str) -> tuple[str, str]:
    """
    Spawn a subagent to perform a task in a specific directory

    Args:
        agent_name: The name of the agent to spawn
        directory: The directory where the agent should operate
        task: The task for the agent to perform

    Returns:
        Tuple of (status_message, unit_name) where unit_name is empty string on error
    """
    try:
        # Resolve the target directory
        target_dir = Path(directory).resolve()

        # Build the claude command with --agent parameter
        # Quote arguments that contain spaces
        def quote_if_needed(arg: str) -> str:
            if " " in arg or '"' in arg:
                # Escape any existing quotes and wrap in quotes
                return '"' + arg.replace('"', '\\"') + '"'
            return arg

        cmd_parts = [_claude_command, "--agent", agent_name, quote_if_needed(task)]
        claude_cmd_str = " ".join(cmd_parts)

        # Execute in terminal
        error_msg, unit_name = execute_in_terminal(claude_cmd_str, str(target_dir))

        if error_msg:
            return (error_msg, "")

        return (f"Agent '{agent_name}' spawned successfully in '{directory}' (Unit: {unit_name}) to perform: {task}", unit_name)

    except Exception as e:
        return (f"Error spawning agent: {e}", "")
