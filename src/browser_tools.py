"""
browser_tools.py
Day 54: optional external research tool. Uses the Tavily search API if
TAVILY_API_KEY is configured; otherwise returns a clear "not configured"
result instead of silently failing or making something up. External
findings are always tagged with their source so the agent can distinguish
internal evidence from external claims (Day 54: source tracking).
"""

from typing import List, Optional

import requests

from . import config

TAVILY_ENDPOINT = "https://api.tavily.com/search"


class ResearchUnavailable(Exception):
    pass


def search_external_information(query: str, max_results: int = 3) -> List[dict]:
    """Returns a list of {title, url, snippet} dicts from external web search.

    Raises ResearchUnavailable if no API key is configured — the agent must
    handle this gracefully (e.g. note in the report that external research
    was unavailable) rather than inventing external factors.
    """
    if not config.TAVILY_API_KEY:
        raise ResearchUnavailable(
            "External research is not configured (no TAVILY_API_KEY set). "
            "Set TAVILY_API_KEY in .env to enable this tool."
        )

    try:
        response = requests.post(
            TAVILY_ENDPOINT,
            json={
                "api_key": config.TAVILY_API_KEY,
                "query": query,
                "max_results": max_results,
                "search_depth": "basic",
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        raise ResearchUnavailable(f"External research request failed: {e}") from e

    results = []
    for item in data.get("results", [])[:max_results]:
        results.append(
            {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "snippet": item.get("content", ""),
                "source": "external_web_search",
            }
        )
    return results
