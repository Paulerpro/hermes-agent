"""MCP server exposing the yfinance-backed tools from tools.py.

Registered with the Hermes Agent framework via ~/.hermes/config.yaml
(mcp_servers.finance) so AIAgent can call these instead of relying on
generic web search for financial data. Run standalone for testing with:

    uv run python finance_mcp_server.py
"""

from fastmcp import FastMCP

import tools

mcp = FastMCP("finance")


@mcp.tool
def get_quote(ticker: str) -> dict:
    """Get the current price, previous close, and day change for a stock.

    Args:
        ticker: Stock ticker symbol, e.g. AAPL.
    """
    return tools.fetch_quote(ticker)


@mcp.tool
def get_fundamentals(ticker: str) -> dict:
    """Get key fundamentals for a stock: market cap, P/E, EPS, dividend yield, sector.

    Args:
        ticker: Stock ticker symbol, e.g. AAPL.
    """
    return tools.fetch_fundamentals(ticker)


@mcp.tool
def get_price_history(ticker: str, period: str = "6mo") -> dict:
    """Get price trend (start/end/high/low/% change) for a stock over a period.

    Args:
        ticker: Stock ticker symbol, e.g. AAPL.
        period: One of 1mo, 3mo, 6mo, 1y, 5y.
    """
    return tools.fetch_price_history(ticker, period)


@mcp.tool
def get_company_news(ticker: str) -> list:
    """Get recent news headlines for a stock.

    Args:
        ticker: Stock ticker symbol, e.g. AAPL.
    """
    return tools.fetch_company_news(ticker)


if __name__ == "__main__":
    mcp.run()
