import httpx
from bs4 import BeautifulSoup
from typing import Optional

NEWS_SEARCH_URL = "https://www.google.com/search"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]


async def search_adverse_media(
    ngo_name: str,
    state: Optional[str] = None,
    max_results: int = 5,
) -> dict:
    """Search for recent news about an NGO.

    Uses Google News search to find recent coverage.
    Returns headlines, snippets, and URLs.
    """
    result = {
        "source": "google_news",
        "ngo_name": ngo_name,
        "results": [],
        "sentiment": "unknown",
        "fetch_method": "scrape",
        "error": None,
    }

    query = f'"{ngo_name}" NGO'
    if state:
        query += f" {state}"

    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            headers = {"User-Agent": USER_AGENTS[0]}

            resp = await client.get(
                NEWS_SEARCH_URL,
                params={"q": query, "tbm": "nws"},
                headers=headers,
            )

            if resp.status_code != 200:
                result["error"] = f"HTTP {resp.status_code} from Google News"
                return result

            soup = BeautifulSoup(resp.text, "html.parser")
            articles = soup.find_all("div", {"class": "SoaBEf"})

            if not articles:
                articles = soup.find_all("div", {"class": "g"})

            results = []
            for article in articles[:max_results]:
                title_el = article.find("div", {"class": "MBeuO"})
                snippet_el = article.find("div", {"class": "GI74Re"})
                link_el = article.find("a")

                entry = {
                    "title": title_el.get_text(strip=True) if title_el else "",
                    "snippet": snippet_el.get_text(strip=True) if snippet_el else "",
                    "url": link_el["href"] if link_el and link_el.get("href") else "",
                }
                if entry["title"]:
                    results.append(entry)

            if results:
                result["results"] = results
                negative_keywords = ["fraud", "scam", "fake", "suspended", "banned", "investigation", "arrest", "corruption"]
                negative_count = sum(
                    1 for r in results
                    for kw in negative_keywords
                    if kw in (r.get("title", "") + r.get("snippet", "")).lower()
                )
                if negative_count > 0:
                    result["sentiment"] = "negative"
                else:
                    result["sentiment"] = "neutral"
            else:
                result["sentiment"] = "no_coverage"

    except httpx.RequestError as e:
        result["error"] = f"Network error: {str(e)}"
    except Exception as e:
        result["error"] = f"Scraping error: {str(e)}"

    return result
