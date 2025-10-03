import signal
import atexit
from fastmcp import FastMCP
from spawn_agent.cgroup import cleanup_systemd_unit, list_spawned_units
from spawn_agent.spawn_subagent import initialize, spawn_subagent

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
def spawn_agent(agent_name: str, directory: str, task: str) -> str:
    """
    Spawn an agent to perform a task in a specific directory

    Args:
        agent_name: The name of the agent to spawn
        directory: The directory where the agent should operate
        task: The task for the agent to perform

    Returns:
        Status message about the spawned agent
    """
    status_message, unit_name = spawn_subagent(agent_name, directory, task)

    # Track the spawned unit for cleanup if successful
    if unit_name:
        global spawned_units
        spawned_units.append(unit_name)

    return status_message


@mcp.tool()
def spawn_session(directory: str) -> str:
    """
    Spawn a new Claude session in a terminal window

    Args:
        directory: The directory where the session should run

    Returns:
        Status message about the spawned session
    """
    from spawn_agent.spawn_subagent import spawn_session as spawn_session_impl
    status_message, unit_name = spawn_session_impl(directory)

    # Track the spawned unit for cleanup if successful
    if unit_name:
        global spawned_units
        spawned_units.append(unit_name)

    return status_message


def main():
    # Find available terminal emulator at startup
    if not initialize():
        print("Warning: No suitable terminal emulator found. spawn_agent functionality will be limited.")

    mcp.run()


if __name__ == "__main__":
    main()