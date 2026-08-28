"""Hermes Agent - a small financial research agent.

Three-stage orchestration (Plan -> Act -> Synthesize) around Mistral's
tool use, in place of one opaque tool-calling loop:

  1. PLAN        - one Mistral call, no tools: sketch what data is needed.
  2. ACT          - manual tool-calling loop: fetch that data via 4 tools.
  3. SYNTHESIZE   - one Mistral call, no tools, schema-enforced JSON output.
"""

import json
import os
import sys

from dotenv import load_dotenv
from mistralai.client import Mistral

import tools

load_dotenv()

MODEL = os.environ.get("MISTRAL_MODEL", "mistral-small-latest")

client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])

FINAL_ANSWER_SCHEMA = {
    "type": "object",
    "properties": {
        "answer": {"type": "string"},
        "tickers_analyzed": {"type": "array", "items": {"type": "string"}},
        "key_metrics": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "label": {"type": "string"},
                    "value": {"type": "string"},
                },
                "required": ["label", "value"],
                "additionalProperties": False,
            },
        },
        "caveats": {"type": "string"},
    },
    "required": ["answer", "tickers_analyzed", "key_metrics", "caveats"],
    "additionalProperties": False,
}

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_quote",
            "description": "Get the current price, previous close, and day change for a stock.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Stock ticker symbol, e.g. AAPL."},
                },
                "required": ["ticker"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_fundamentals",
            "description": "Get key fundamentals for a stock: market cap, P/E, EPS, dividend yield, sector.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Stock ticker symbol, e.g. AAPL."},
                },
                "required": ["ticker"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_price_history",
            "description": "Get price trend (start/end/high/low/% change) for a stock over a period.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Stock ticker symbol, e.g. AAPL."},
                    "period": {
                        "type": "string",
                        "description": "One of 1mo, 3mo, 6mo, 1y, 5y.",
                        "default": "6mo",
                    },
                },
                "required": ["ticker"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_company_news",
            "description": "Get recent news headlines for a stock.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Stock ticker symbol, e.g. AAPL."},
                },
                "required": ["ticker"],
            },
        },
    },
]

TOOL_DISPATCH = {
    "get_quote": lambda args: tools.fetch_quote(args["ticker"]),
    "get_fundamentals": lambda args: tools.fetch_fundamentals(args["ticker"]),
    "get_price_history": lambda args: tools.fetch_price_history(args["ticker"], args.get("period", "6mo")),
    "get_company_news": lambda args: tools.fetch_company_news(args["ticker"]),
}


def plan(question: str) -> str:
    response = client.chat.complete(
        model=MODEL,
        max_tokens=1024,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a financial research planner. Given a user's question, write "
                    "a short plan (2-4 bullet points) naming the ticker(s) involved and "
                    "which kinds of data are needed to answer it (quote, fundamentals, "
                    "price history, news). Do not answer the question yet - only plan."
                ),
            },
            {"role": "user", "content": question},
        ],
    )
    return response.choices[0].message.content


def act(question: str, research_plan: str, call_log: list) -> str:
    messages = [
        {
            "role": "system",
            "content": (
                "You are a financial research agent. Use the available tools to gather "
                "the data called for in the research plan, then give a brief "
                "natural-language summary of what you found. Only call tools relevant "
                "to the question."
            ),
        },
        {
            "role": "user",
            "content": f"Question: {question}\n\nResearch plan:\n{research_plan}",
        },
    ]

    for _ in range(8):  # hard cap to guard against runaway tool-call loops
        response = client.chat.complete(
            model=MODEL,
            max_tokens=16000,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
            messages=messages,
        )
        message = response.choices[0].message
        messages.append(message)

        if not message.tool_calls:
            return message.content or ""

        for tool_call in message.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            result = TOOL_DISPATCH[name](args)
            call_log.append({"tool": name, "input": args, "output": result})
            messages.append({
                "role": "tool",
                "name": name,
                "content": json.dumps(result, default=str),
                "tool_call_id": tool_call.id,
            })

    return ""


def synthesize(question: str, research_plan: str, call_log: list, act_summary: str) -> dict:
    evidence = json.dumps(call_log, indent=2, default=str)
    response = client.chat.complete(
        model=MODEL,
        max_tokens=2048,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a financial research analyst. Using the research plan, the "
                    "raw tool data gathered, and the draft summary, produce a final "
                    "structured answer to the user's original question. Ground every "
                    "number in the tool data provided - never invent figures. If a tool "
                    "call returned an error, acknowledge the gap in caveats."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Original question: {question}\n\n"
                    f"Research plan:\n{research_plan}\n\n"
                    f"Tool data gathered:\n{evidence}\n\n"
                    f"Draft summary:\n{act_summary}"
                ),
            },
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "final_answer",
                "schema": FINAL_ANSWER_SCHEMA,
                "strict": True,
            },
        },
    )
    text = response.choices[0].message.content
    return json.loads(text)


def research(question: str) -> dict:
    call_log: list = []
    research_plan = plan(question)
    act_summary = act(question, research_plan, call_log)
    result = synthesize(question, research_plan, call_log, act_summary)
    return {"plan": research_plan, "tool_calls": call_log, "result": result}


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "How has Apple's stock performed this year and is it fundamentally healthy?"

    output = research(question)

    print("=== PLAN ===")
    print(output["plan"])

    print("\n=== TOOL CALLS ===")
    for c in output["tool_calls"]:
        print(f"- {c['tool']}({c['input']})")

    print("\n=== FINAL ANSWER ===")
    print(json.dumps(output["result"], indent=2))
