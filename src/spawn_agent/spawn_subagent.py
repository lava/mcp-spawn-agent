import subprocess
from pathlib import Path
from spawn_agent.cgroup import execute_with_systemd_run

# Global terminal command - selected once at startup
TERMINAL_CMD = None


def find_available_terminal():
    """Find the first available terminal emulator on the system"""
    terminal_options = [
        ["gnome-terminal", "--working-directory", "{dir}", "--", "bash", "-c", "{cmd}"],
        ["konsole", "--workdir", "{dir}", "-e", "bash", "-c", "{cmd}; read -p 'Press Enter to close...'"],
        ["xterm", "-e", "cd '{dir}' && {cmd}; read -p 'Press Enter to close...'"],
        ["x-terminal-emulator", "-e", "bash -c 'cd \"{dir}\" && {cmd}; read -p \"Press Enter to close...\"'"]
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
        if not target_dir.exists():
            return (f"Error: Directory '{directory}' does not exist", "")

        # Find the agent definition
        try:
            agent_definition = find_agent_definition(agent_name, str(target_dir))
        except FileNotFoundError as e:
            return (f"Error: {e}", "")

        # Prepare the system prompt with agent definition appended
        system_prompt_addition = f"{agent_definition}"

        # Check if terminal is available
        if TERMINAL_CMD is None:
            return ("Error: No suitable terminal emulator found. Please install gnome-terminal, konsole, xterm, or another terminal emulator.", "")

        # Prepare the claude command string
        claude_cmd_str = " ".join([
            f'"{arg}"' if " " in arg else arg
            for arg in [
                "/home/benno/.claude/local/claude",
                "--append-system-prompt", system_prompt_addition,
                task
            ]
        ])

        # Build terminal command with placeholders filled
        terminal_cmd = []
        for part in TERMINAL_CMD:
            if "{dir}" in part:
                terminal_cmd.append(part.replace("{dir}", str(target_dir)))
            elif "{cmd}" in part:
                terminal_cmd.append(part.replace("{cmd}", claude_cmd_str))
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

        return (f"Agent '{agent_name}' spawned successfully in '{directory}' (Unit: {unit_name}) to perform: {task}", unit_name)

    except Exception as e:
        return (f"Error spawning agent: {e}", "")
