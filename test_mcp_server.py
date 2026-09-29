from pathlib import Path

from mcp_server import discover_agents, invoke_agent


def test_discover_agents_lists_workspace_agents():
    root = Path(__file__).resolve().parent
    agents = discover_agents(root)
    names = {agent["name"] for agent in agents}
    assert "agent-builder" in names
    assert any(agent["runner_type"] in {"python", "node"} for agent in agents)


def test_invoke_builder_agent_runs_successfully():
    result = invoke_agent("agent-builder", {"goal": "Test MCP integration", "targets": ["agent-builder"]})
    assert result["status"] == "success"
    assert "Test MCP integration" in result["summary"]
    assert result["plan"]


def test_orchestrate_agents_returns_aggregate_result():
    from mcp_server import orchestrate_agents

    result = orchestrate_agents(["agent-builder"], {"goal": "Test orchestration", "targets": ["agent-builder"]})
    assert result["status"] == "success"
    assert result["agents"] == ["agent-builder"]
    assert len(result["results"]) == 1
    assert result["results"][0]["status"] == "success"


def test_build_server_manifest_has_client_ready_metadata():
    from mcp_server import build_server_manifest

    manifest = build_server_manifest()
    assert manifest["name"]
    assert "stdio" in manifest["transports"]
    assert "streamable-http" in manifest["transports"]
    assert manifest["supported_tools"]



# COPYRIGHT 2026 By Orville Arrindell. All rights reserved.