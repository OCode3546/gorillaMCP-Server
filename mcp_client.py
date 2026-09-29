#!/usr/bin/env python3
"""FastMCP stdio client for the workspace agent registry.

This project uses the official FastMCP client API to connect to the local server
that is defined in mcp_server.py. It is the supported client path for this SDK.

Examples:
    python mcp_client.py --list
    python mcp_client.py --call list_agents
    python mcp_client.py --call run_agent_tool --arg agent_name=file-sorter-agent --arg goal='Sort files' --arg targets='["./"]'
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

from fastmcp import Client
from fastmcp.client.transports import StdioTransport

WORKSPACE_ROOT = Path(__file__).resolve().parent
SERVER_PATH = WORKSPACE_ROOT / "mcp_server.py"
VENV_PYTHON = WORKSPACE_ROOT / ".venv" / ("Scripts" if os.name == "nt" else "bin") / ("python.exe" if os.name == "nt" else "python")
SERVER_PYTHON = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable


def _make_client() -> Client:
    transport = StdioTransport(
        command=SERVER_PYTHON,
        args=[str(SERVER_PATH), "--transport", "stdio"],
        cwd=str(WORKSPACE_ROOT),
        env={**os.environ},
    )
    return Client(transport)


def _parse_json_arg(value: str) -> Any:
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


async def _async_list_tools() -> list[str]:
    async with _make_client() as client:
        tools = await client.list_tools()
        return [tool.name for tool in tools]


async def _async_call_tool(name: str, arguments: dict[str, Any]) -> Any:
    async with _make_client() as client:
        result = await client.call_tool(name, arguments)
        payload = {
            "is_error": getattr(result, "is_error", False),
            "structured_content": getattr(result, "structured_content", None),
            "content": [
                item.model_dump() if hasattr(item, "model_dump") else str(item)
                for item in getattr(result, "content", [])
            ],
        }
        return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="FastMCP client for the workspace agent registry")
    parser.add_argument("--list", action="store_true", help="List tools available from the server")
    parser.add_argument("--call", metavar="TOOL_NAME", help="Call a named tool")
    parser.add_argument("--arg", action="append", default=[], help="Arguments passed as key=value. JSON values are parsed automatically.")
    args = parser.parse_args()

    if not args.list and not args.call:
        parser.print_help()
        return 1

    async def runner() -> int:
        if args.list:
            tools = await _async_list_tools()
            print(json.dumps({"tools": tools}, indent=2))
            return 0

        if args.call:
            kwargs: dict[str, Any] = {}
            for item in args.arg:
                if "=" not in item:
                    raise ValueError(f"Invalid --arg value {item!r}; expected key=value")
                key, value = item.split("=", 1)
                kwargs[key] = _parse_json_arg(value)

            result = await _async_call_tool(args.call, kwargs)
            print(json.dumps(result, indent=2, default=str))
            return 0

        return 1

    try:
        return asyncio.run(runner())
    except Exception as exc:
        print(f"MCP client error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())





# COPYRIGHT 2026 By Orville Arrindell. All rights reserved.