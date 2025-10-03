import signal
import atexit
import subprocess
from fastmcp import FastMCP
from spawn_agent.cgroup import cleanup_systemd_unit, list_spawned_units
from spawn_agent.terminal import initialize
from spawn_agent.spawn_subagent import spawn_subagent as spawn_subagent_impl
from spawn_agent.spawn_session import spawn_session as spawn_session_impl, set_claude_command

mcp = FastMCP("spawn-agent")

# Global list to track spawned systemd units
spawned_units: list[str] = []


def cleanup_spawned_processes():
    """Clean up all spawned systemd units"""
    # Clean up units we've tracked
    # with open("output.txt", "a") as f:
    #     f.write(f"cleaning up units {spawned_units}\n")
    for unit_name in spawned_units:
        try:
            cleanup_systemd_unit(unit_name)
        except OSError:
            # Unit might not exist or already cleaned up
            pass
    spawned_units.clear()
    
    # Also clean up any spawn-agent units that might have been missed
    try:
        all_units = list_spawned_units()
        for unit_name in all_units:
            try:
                cleanup_systemd_unit(unit_name)
            except OSError:
                pass
    except OSError:
        # If we can't list units, just continue
        pass


def handle_signal(signum, frame):
    """Handle termination signals"""
    cleanup_spawned_processes()
    exit(0)


# Register cleanup functions
atexit.register(cleanup_spawned_processes)
signal.signal(signal.SIGTERM, handle_signal)
signal.signal(signal.SIGINT, handle_signal)


@mcp.tool()
def spawn_subagent(agent_name: str, directory: str, task: str) -> str:
    """
    Spawn an subagent to perform a task in a specific directory

    Args:
        agent_name: The name of the agent to spawn
        directory: The directory where the agent should operate
        task: The task for the agent to perform
    """
    status_message, unit_name = spawn_subagent_impl(agent_name, directory, task)

    # Track the spawned unit for cleanup if successful
    if unit_name:
        global spawned_units
        spawned_units.append(unit_name)

    return status_message


@mcp.tool()
def spawn_session(directory: str, driver: str = "claude", model: str | None = None) -> str:
    """
    Spawn a new claude session in another terminal window

    Args:
        directory: The directory where the session should run
        driver: The CLI driver to use - "claude", "codex", or "crush" (default: "claude").
                Usually left empty; only specify on explicit user request.
        model: Model name to use with "claude" driver (suggested: "qwen", "sonnet", "deepseek").
               Usually left empty; only specify on explicit user request.
    """
    status_message, unit_name = spawn_session_impl(directory, driver, model)
    # Note: We don't track spawn_session units for cleanup - they persist independently
    return status_message


def resolve_claude_command() -> str:
    """Resolve the 'claude' shell alias to the actual command"""
    try:
        # Use bash to expand the alias
        result = subprocess.run(
            ["bash", "-i", "-c", "type -a claude"],
            capture_output=True,
            text=True,
            timeout=2
        )

        if result.returncode == 0:
            # Parse output like "claude is aliased to `ccr code'"
            for line in result.stdout.splitlines():
                if "is aliased to" in line:
                    # Extract the command from the alias
                    alias_def = line.split("is aliased to", 1)[1].strip()
                    # Remove backticks if present
                    return alias_def.strip("`'\"")

        # Fall back to checking if 'claude' exists as a command
        which_result = subprocess.run(
            ["which", "claude"],
            capture_output=True,
            text=True,
            timeout=2
        )
        if which_result.returncode == 0:
            return which_result.stdout.strip()
    except (subprocess.TimeoutExpired, OSError):
        pass

    # Default fallback
    return "claude"


def main():
    # Find available terminal emulator at startup
    if not initialize():
        print("Warning: No suitable terminal emulator found. spawn_agent functionality will be limited.")

    # Resolve the claude command/alias
    claude_cmd = resolve_claude_command()
    set_claude_command(claude_cmd)

    mcp.run()


if __name__ == "__main__":
    main()
