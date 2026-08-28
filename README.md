# Financial Research Agent

A financial research agent built on [Nous Research's Hermes Agent](https://hermes-agent.nousresearch.com/docs/guides/python-library)
framework, routed through [OpenRouter](https://openrouter.ai/) to a free
model so it costs nothing to run. Financial data comes from real
[yfinance](https://github.com/ranaroussi/yfinance) calls, exposed to the
agent as an MCP server — not from the model's own knowledge.

Hermes Agent isn't a pip package — it's cloned and run from its own
directory, and its `AIAgent` class handles the full plan/tool-call/respond
loop internally. [finance_app.py](finance_app.py) (copied into the cloned
framework as a setup step) wraps that in a finance-focused entrypoint.

## How it fits together

- [tools.py](tools.py) — plain Python functions backed by `yfinance`
  (quote, fundamentals, price history, news).
- [finance_mcp_server.py](finance_mcp_server.py) — a [FastMCP](https://gofastmcp.com/)
  server that exposes those functions as MCP tools.
- Hermes Agent's global config (`mcp_servers.finance`, see setup below)
  tells it to launch that server and register its tools.
- [finance_app.py](finance_app.py) constructs `AIAgent` with
  `enabled_toolsets=["finance"]`, so the model can only answer using real
  tool calls to that MCP server — not its own training-data guesses.

## Setup

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

**1. Clone the framework** (not committed to this repo — see [.gitignore](.gitignore)):

```bash
git clone https://github.com/NousResearch/hermes-agent.git vendor/hermes-agent-framework
```

**2. Install its dependencies (including the `mcp` extra) and copy in the entrypoint:**

```bash
cp finance_app.py vendor/hermes-agent-framework/
cd vendor/hermes-agent-framework
uv sync --extra mcp
```

The `mcp` extra is required — without it, Hermes Agent silently skips all
MCP server discovery (no error, it just won't have the finance tools).

**3. Install this project's own dependencies** (yfinance + fastmcp, for the MCP server):

```bash
cd ../..   # back to the repo root
uv sync
```

**4. Set your OpenRouter API key** (inside the framework directory):

```bash
cp .env.example vendor/hermes-agent-framework/.env
# edit vendor/hermes-agent-framework/.env and paste in your OPENROUTER_API_KEY
```

`finance_app.py` and `.env` both need to live inside
`vendor/hermes-agent-framework/` — that directory is gitignored (it's a
clone of a separate third-party repo with its own git history), so these
copy steps re-create what git won't track there.

Get a free key at the [OpenRouter dashboard](https://openrouter.ai/keys).
The default model (`OPENROUTER_MODEL=minimax/minimax-m3:free`) costs nothing to
call — check [openrouter.ai/models?max_price=0](https://openrouter.ai/models?max_price=0)
for the current list of free models if you want to swap it.

**5. Register the finance MCP server.** Hermes Agent reads MCP servers
from a machine-global config file (not part of this repo):
- Windows: `%LOCALAPPDATA%\hermes\config.yaml`
- macOS/Linux: `~/.hermes/config.yaml`

Create it with:

```yaml
mcp_servers:
  finance:
    command: "uv"
    args:
      - "run"
      - "--project"
      - "<absolute path to this repo>"
      - "python"
      - "<absolute path to this repo>/finance_mcp_server.py"

tools:
  tool_search:
    # Only 4 small finance tools — expose them directly instead of via the
    # tool_search/tool_call indirection bridge (meant for large tool
    # catalogs), which weaker free models handle unreliably.
    enabled: "off"
```

Use forward slashes in the paths even on Windows (YAML-friendly), e.g.
`C:/Users/you/hermes-agent`.

## Usage

Run from inside the cloned framework directory (its internal imports
depend on it):

```bash
cd vendor/hermes-agent-framework
uv run python finance_app.py "How has Apple's stock performed this year and is it fundamentally healthy?"
```

With no arguments it runs a default sample question.

**If you get an HTTP 429 rate-limit error**, the free model you're on is
temporarily oversubscribed upstream (common — free models are shared
across everyone using them). Swap `OPENROUTER_MODEL` in `.env` to another
`:free` id from [openrouter.ai/models?max_price=0](https://openrouter.ai/models?max_price=0)
and retry.

**If the agent says it has no tools / an "unknown toolset" warning
appears**, double check step 5 — the `mcp_servers.finance` config wasn't
found or the `mcp` extra (step 2) wasn't installed.

## Project layout

- [finance_app.py](finance_app.py) — the entrypoint this project adds to
  the framework. Tracked here; copied into
  `vendor/hermes-agent-framework/` (gitignored) as a setup step, since
  that's where it needs to run from.
- [finance_mcp_server.py](finance_mcp_server.py) — FastMCP server exposing
  `tools.py`'s fetchers as MCP tools for the agent to call.
- [tools.py](tools.py) — plain, provider-agnostic data fetchers backed by
  `yfinance` (price quotes, fundamentals, price history, news).

## Configuration

| Env var           | Description                                        | Default            |
|--------------------|-----------------------------------------------------|---------------------|
| `OPENROUTER_API_KEY` | Your OpenRouter API key (required)                 | —                   |
| `OPENROUTER_MODEL`   | OpenRouter model id to use                         | `minimax/minimax-m3:free` |

Set both in `vendor/hermes-agent-framework/.env` (that's where the
framework's own env loader looks, relative to where you run it from).
