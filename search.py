"""Web search via DuckDuckGo (no API key)."""
from ddgs import DDGS


def web_search(query: str, max_results: int = 4) -> list[dict]:
    """Returns a list of {title, url, snippet}. Returns [] on network errors."""
    try:
        results = DDGS().text(query, max_results=max_results)
    except Exception as e:
        print(f"  search failed for '{query}': {e}")
        return []
    return [
        {"title": r.get("title", ""), "url": r.get("href", ""), "snippet": r.get("body", "")}
        for r in results
    ]
