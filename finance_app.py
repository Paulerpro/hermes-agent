"""Hermes Agent (Nous Research) financial research entrypoint.

Uses the NousResearch/hermes-agent framework's AIAgent, routed through
OpenRouter to a free model, as the agentic engine — replacing the
hand-rolled Plan/Act/Synthesize loop from the earlier prototype.

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

    agent = AIAgent(
        model=MODEL,
        provider="openrouter",
        quiet_mode=True,
        enabled_toolsets=["web"],
    )
    answer = agent.chat(question)
    print(answer)


if __name__ == "__main__":
    main()
