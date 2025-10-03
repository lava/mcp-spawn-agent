from pathlib import Path
from spawn_agent.terminal import execute_in_terminal


def find_agent_definition(agent_name: str, start_directory: str) -> str:
    """
    Recursively search for agent definition file up the directory tree until HOME

    Args:
        agent_name: The name of the agent to find
        start_directory: Directory to start searching from

    Returns:
        Content of the agent definition file

    Raises:
        FileNotFoundError: If agent definition is not found
    """
    home_dir = Path.home()
    current_dir = Path(start_directory).resolve()

    while current_dir >= home_dir:
        agent_file = current_dir / ".claude" / "agents" / f"{agent_name}.md"
        if agent_file.exists():
            return agent_file.read_text()

        if current_dir == home_dir:
            break
        current_dir = current_dir.parent

    raise FileNotFoundError(f"Agent definition '{agent_name}.md' not found in .claude/agents/ from {start_directory} up to HOME")


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

        # Find the agent definition
        try:
            agent_definition = find_agent_definition(agent_name, str(target_dir))
        except FileNotFoundError as e:
            return (f"Error: {e}", "")

        # Prepare the system prompt with agent definition appended
        system_prompt_addition = f"{agent_definition}"

        # Prepare the claude command string
        claude_cmd_str = " ".join([
            f'"{arg}"' if " " in arg else arg
            for arg in [
                "/home/benno/.claude/local/claude",
                "--append-system-prompt", system_prompt_addition,
                task
            ]
        ])

        # Execute in terminal
        error_msg, unit_name = execute_in_terminal(claude_cmd_str, directory)

        if error_msg:
            return (error_msg, "")

        return (f"Agent '{agent_name}' spawned successfully in '{directory}' (Unit: {unit_name}) to perform: {task}", unit_name)

    except Exception as e:
        return (f"Error spawning agent: {e}", "")
