"""Hermes Agent (Nous Research) financial research entrypoint.

Uses the NousResearch/hermes-agent framework's AIAgent, routed through
OpenRouter to a free model, as the agentic engine — replacing the
hand-rolled Plan/Act/Synthesize loop from the earlier prototype.

Data comes from the yfinance-backed tools in tools.py, exposed as an MCP
server (finance_mcp_server.py) and registered in the framework's global
config (~/.hermes/config.yaml or, on Windows, %LOCALAPPDATA%\\hermes\\
config.yaml, under mcp_servers.finance — see README).

This file lives here in version control, but must be copied into (and run
from inside) the cloned vendor/hermes-agent-framework/ directory — its
`from run_agent import AIAgent` and the framework's own env/log loading
rely on that being the working directory. See README for setup steps.
"""

import os
import sys

from run_agent import AIAgent

MODEL = os.environ.get("OPENROUTER_MODEL", "minimax/minimax-m3:free")


def main() -> None:
    question = " ".join(sys.argv[1:]) or (
        "How has Apple's stock performed this year and is it fundamentally healthy?"
    )

    # MCP servers (our "finance" toolset) are registered lazily in the
    # background; the CLI blocks on this same call at its own startup so
    # tools are actually ready before the agent runs (see hermes_cli/main.py).
    from tools.mcp_tool import discover_mcp_tools
    discover_mcp_tools()

    agent = AIAgent(
        model=MODEL,
        provider="openrouter",
        quiet_mode=True,
        enabled_toolsets=["finance"],
    )
    answer = agent.chat(question)
    print(answer)


if __name__ == "__main__":
    main()
