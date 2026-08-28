# Hermes Agent

A small financial research agent built around a three-stage
Plan -> Act -> Synthesize orchestration, using [Mistral AI](https://mistral.ai)
for the LLM calls and [yfinance](https://github.com/ranaroussi/yfinance) for
market data.

1. **Plan** — one Mistral call, no tools: sketch what data is needed to
   answer the question.
2. **Act** — a tool-calling loop: Mistral decides which of four tools to
   call (quote, fundamentals, price history, news) and the loop executes
   them against `yfinance`.
3. **Synthesize** — one Mistral call, no tools, with a JSON-schema-enforced
   response, that turns the plan + gathered data into a structured answer.

## Setup

Requires Python 3.10+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

Then set your Mistral API key:

```bash
cp .env.example .env
# edit .env and paste in your MISTRAL_API_KEY
```

Get a free API key from the [Mistral console](https://console.mistral.ai/).
The default model (`mistral-small-latest`) works with Mistral's free tier.

## Usage

```bash
uv run agent.py "How has Apple's stock performed this year and is it fundamentally healthy?"
```

With no arguments it runs a default sample question.

## Project layout

- [agent.py](agent.py) — orchestration (plan / act / synthesize) and the
  Mistral tool-calling loop.
- [tools.py](tools.py) — plain, provider-agnostic data fetchers backed by
  `yfinance` (price quotes, fundamentals, price history, news).

## Configuration

| Env var           | Description                              | Default                |
|--------------------|-------------------------------------------|-------------------------|
| `MISTRAL_API_KEY`  | Your Mistral API key (required)           | —                       |
| `MISTRAL_MODEL`    | Mistral model to use                      | `mistral-small-latest`  |
