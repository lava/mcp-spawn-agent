# mcp-spawn-agent

An MCP server that provides tools for spawning Claude agents and sessions in separate terminal windows.

## MCP Tools

### spawn_session

Spawn a new Claude session in another terminal window.

**Parameters:**
- `directory` (string): The directory where the session should run
- `driver` (string, optional): The CLI driver to use - "claude", "codex", or "crush" (default: "claude"). Usually left empty; only specify on explicit user request.
- `model` (string, optional): Model name to use with "claude" driver (suggested: "qwen", "sonnet", "deepseek"). Usually left empty; only specify on explicit user request.

**Usage:** Use this tool to open an interactive Claude session in a new terminal window for the user to interact with directly.

### spawn_subagent

Spawn a subagent to perform a task in a specific directory.

**Parameters:**
- `agent_name` (string): The name of the agent to spawn
- `directory` (string): The directory where the agent should operate
- `task` (string): The task for the agent to perform

**Usage:** Use this tool when you need to delegate a specific task to another agent instance running in its own environment.
