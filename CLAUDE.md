# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an MCP (Model Context Protocol) server built with FastMCP that provides tools for spawning Claude agents and sessions in separate terminal windows. It exposes two main tools:
- `spawn_subagent`: Spawns a Claude instance with a custom agent definition to perform a specific task
- `spawn_session`: Opens an interactive Claude session in a new terminal window

## Architecture

- **FastMCP Server**: The core server is defined in `src/spawn_agent/server.py:9` using the FastMCP framework
- **Two Tool Pattern**: The server exposes `spawn_subagent` and `spawn_session` tools
- **Process Management**: Uses systemd-run to spawn isolated processes in separate terminal windows
- **Agent Definitions**: Loads agent definitions from `.claude/agents/` directory (searched up to HOME)
- **Cleanup Handling**: Tracks spawned units and cleans them up on exit via atexit handlers and signal handling
- **Package Structure**: Modular design with separate files for each concern:
  - `server.py`: FastMCP server and tool definitions
  - `spawn_subagent.py`: Subagent spawning logic and agent definition loading
  - `spawn_session.py`: Session spawning with driver/model support
  - `terminal.py`: Terminal emulator detection and process execution
  - `cgroup.py`: Systemd unit management and cleanup

## Development Commands

```bash
# Install dependencies and sync environment
uv sync

# Run the MCP server directly
uv run python -m spawn_agent.server

# Run via entry point (after syncing)
uv run mcp-spawn-agent

# Build the package
uv build
```

## Key Implementation Details

### Server Configuration
- Server is initialized with the name "spawn-agent" in `src/spawn_agent/server.py:9`
- Entry point is configured in `pyproject.toml` to run `spawn_agent.server:main`
- Terminal emulator is detected at startup via `terminal.initialize()` at `src/spawn_agent/server.py:92`

### Tool Functions
- `spawn_subagent()` at `src/spawn_agent/server.py:54`: Spawns Claude with agent definition
- `spawn_session()` at `src/spawn_agent/server.py:74`: Opens interactive Claude session
- Both tools track spawned systemd units for cleanup (except spawn_session which persists)

### Agent Definition Search
- Looks for `.claude/agents/{agent_name}.md` files in `spawn_subagent.py:23-29`
- Searches recursively from target directory up to HOME directory
- Returns FileNotFoundError if agent definition not found

### Process Isolation
- Uses `systemd-run --user --scope` to create isolated process groups
- Spawns processes in separate terminal windows (gnome-terminal, konsole, xterm, etc.)
- Cleanup is handled via atexit and signal handlers (SIGTERM, SIGINT)

## Code Style and Best Practices

- Always use absolute imports from the project root