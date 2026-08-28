# Hermes Agent

A financial research agent built on [Nous Research's Hermes Agent](https://hermes-agent.nousresearch.com/docs/guides/python-library)
framework, routed through [OpenRouter](https://openrouter.ai/) to a free
model so it costs nothing to run.

Hermes Agent isn't a pip package — it's cloned and run from its own
directory, and its `AIAgent` class handles the full plan/tool-call/respond
loop internally. [finance_app.py](vendor/hermes-agent-framework/finance_app.py)
(added by this project into the cloned framework) wraps that in a
finance-focused entrypoint.

> Custom financial data tools (the yfinance-backed fetchers in
> [tools.py](tools.py)) aren't wired in yet — the agent currently answers
> using Hermes Agent's built-in `web` toolset. Hooking `tools.py` up as an
> MCP server is a planned next step.

## Setup

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

**1. Clone the framework** (not committed to this repo — see [.gitignore](.gitignore)):

```bash
git clone https://github.com/NousResearch/hermes-agent.git vendor/hermes-agent-framework
```

**2. Install its dependencies and copy in the entrypoint:**

```bash
cp finance_app.py vendor/hermes-agent-framework/
cd vendor/hermes-agent-framework
uv sync
```

**3. Set your OpenRouter API key:**

```bash
cp ../../.env.example .env
# edit .env and paste in your OPENROUTER_API_KEY
```

`finance_app.py` and `.env` both need to live inside
`vendor/hermes-agent-framework/` — that directory is gitignored (it's a
clone of a separate third-party repo with its own git history), so these
two copy steps re-create what git won't track there.

Get a free key at the [OpenRouter dashboard](https://openrouter.ai/keys).
The default model (`OPENROUTER_MODEL=minimax/minimax-m3:free`) costs nothing to
call — check [openrouter.ai/models?max_price=0](https://openrouter.ai/models?max_price=0)
for the current list of free models if you want to swap it.

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

## Project layout

- [finance_app.py](finance_app.py) — the entrypoint this project adds to
  the framework. Tracked here; copied into
  `vendor/hermes-agent-framework/` (gitignored) as a setup step, since
  that's where it needs to run from.
- [tools.py](tools.py) — plain, provider-agnostic data fetchers backed by
  `yfinance` (price quotes, fundamentals, price history, news). Not yet
  wired into the agent — see the note above.

## Configuration

| Env var           | Description                                        | Default            |
|--------------------|-----------------------------------------------------|---------------------|
| `OPENROUTER_API_KEY` | Your OpenRouter API key (required)                 | —                   |
| `OPENROUTER_MODEL`   | OpenRouter model id to use                         | `minimax/minimax-m3:free` |

Set both in `vendor/hermes-agent-framework/.env` (that's where the
framework's own env loader looks, relative to where you run it from).
