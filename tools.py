"""Financial data fetchers backed by yfinance.

Plain functions (no Claude/tool decorators here) so they can be tested or
reused independently of the agent orchestration in agent.py.
"""

import yfinance as yf


def fetch_quote(ticker: str) -> dict:
    """Current price snapshot for a ticker."""
    try:
        info = yf.Ticker(ticker).info
        return {
            "ticker": ticker,
            "price": info.get("currentPrice") or info.get("regularMarketPrice"),
            "previous_close": info.get("previousClose"),
            "day_change_pct": info.get("regularMarketChangePercent"),
            "volume": info.get("volume"),
            "currency": info.get("currency"),
        }
    except Exception as e:
        return {"ticker": ticker, "error": str(e)}


def fetch_fundamentals(ticker: str) -> dict:
    """Key valuation/fundamental metrics for a ticker."""
    try:
        info = yf.Ticker(ticker).info
        return {
            "ticker": ticker,
            "company_name": info.get("longName"),
            "sector": info.get("sector"),
            "market_cap": info.get("marketCap"),
            "trailing_pe": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "eps": info.get("trailingEps"),
            "dividend_yield": info.get("dividendYield"),
        }
    except Exception as e:
        return {"ticker": ticker, "error": str(e)}


def fetch_price_history(ticker: str, period: str = "6mo") -> dict:
    """Price trend over a period, e.g. period='1mo'/'6mo'/'1y'."""
    try:
        hist = yf.Ticker(ticker).history(period=period)
        if hist.empty:
            return {"ticker": ticker, "period": period, "error": "no price data returned"}
        start, end = float(hist["Close"].iloc[0]), float(hist["Close"].iloc[-1])
        return {
            "ticker": ticker,
            "period": period,
            "start_price": round(start, 2),
            "end_price": round(end, 2),
            "pct_change": round((end - start) / start * 100, 2),
            "period_high": round(float(hist["Close"].max()), 2),
            "period_low": round(float(hist["Close"].min()), 2),
        }
    except Exception as e:
        return {"ticker": ticker, "period": period, "error": str(e)}


def fetch_company_news(ticker: str, limit: int = 5) -> list:
    """Recent headlines for a ticker."""
    try:
        items = yf.Ticker(ticker).news or []
        headlines = []
        for item in items[:limit]:
            # yfinance has shipped both a flat shape and a nested "content" shape
            # for this endpoint - handle both rather than pin to one.
            content = item.get("content", item)
            provider = content.get("provider")
            link = content.get("canonicalUrl")
            headlines.append({
                "title": content.get("title"),
                "publisher": provider.get("displayName") if isinstance(provider, dict) else content.get("publisher"),
                "link": link.get("url") if isinstance(link, dict) else content.get("link"),
            })
        return headlines
    except Exception as e:
        return [{"ticker": ticker, "error": str(e)}]
