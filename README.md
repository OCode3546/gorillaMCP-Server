# Workspace Agent MCP Server

This folder contains a local MCP server ([mcp_server.py](mcp_server.py)) that exposes the agents in this workspace (`agent-builder`, `code-errors-agent`, `file-sorter-agent`) over stdio or streamable HTTP.

It exposes:

- Tools: `list_agents`, `get_agent`, `run_agent_tool`, `orchestrate_agents_tool`
- Prompt: `agent_task_prompt`
- Resources: `agent://index`, `agent://{agent_name}`, `manifest://server`

Relative `targets` passed to the tools are resolved against this folder, regardless of where the client launches the server from.

## Setup

The server runs from the local virtualenv, which has `fastmcp` installed:

```bash
.venv/bin/python mcp_server.py --transport stdio
```

## Registered clients

- **Claude Code**: [.mcp.json](.mcp.json) (project scope). Claude Code asks you to approve the server the first time you open this folder; check it with `/mcp`.
- **Claude Desktop**: added under `mcpServers` in `~/Library/Application Support/Claude/claude_desktop_config.json`. Fully quit and reopen Claude Desktop after changing it.
- **VS Code (Copilot MCP)**: [.vscode/mcp.json](.vscode/mcp.json).

If you move this folder, update the absolute paths in `.mcp.json` and the Claude Desktop config.

## Streamable HTTP

```bash
.venv/bin/python mcp_server.py --transport streamable-http --host 127.0.0.1 --port 8000
```

The endpoint is `http://127.0.0.1:8000/mcp`. The server has **no authentication**, so do not expose it publicly without putting an authenticating reverse proxy in front of it. [.vscode/mcp.remote.json](.vscode/mcp.remote.json) is an example of a remote client config for that setup.

## Testing

```bash
.venv/bin/python mcp_client.py --list
.venv/bin/python mcp_client.py --call run_agent_tool --arg agent_name=file-sorter-agent --arg goal='Sort files' --arg targets='["agent-builder"]'
```

## Copyright

Copyright 2026 By Orville Arrindell. All rights reserved.
