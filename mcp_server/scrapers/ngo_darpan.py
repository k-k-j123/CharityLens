import httpx
from bs4 import BeautifulSoup
from typing import Optional

NGODARPAN_SEARCH_URL = "https://ngodarpan.gov.in/index.php/search/search_ngo"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]


async def get_ngo_darpan_details(
    ngo_name: Optional[str] = None,
    state: Optional[str] = None,
    registration_number: Optional[str] = None,
) -> dict:
    """Fetch NGO details from NGO Darpan (NITI Aayog) portal.

    Returns registration details, sector, and organizational metadata.
    """
    result = {
        "source": "ngodarpan.gov.in",
        "ngo_name": ngo_name,
        "registration_number": registration_number,
        "state": state,
        "details": None,
        "fetch_method": "scrape",
        "error": None,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            headers = {"User-Agent": USER_AGENTS[0]}

            if registration_number:
                detail_url = f"https://ngodarpan.gov.in/index.php/search/search_ngo/{registration_number}"
                resp = await client.get(detail_url, headers=headers)
            elif ngo_name:
                resp = await client.post(
                    NGODARPAN_SEARCH_URL,
                    data={"ngo_name": ngo_name, "state": state or ""},
                    headers=headers,
                )
            else:
                result["error"] = "Provide either registration_number or ngo_name"
                return result

            if resp.status_code != 200:
                result["error"] = f"HTTP {resp.status_code} from NGO Darpan"
                return result

            soup = BeautifulSoup(resp.text, "html.parser")
            table = soup.find("table", {"class": "table"})

            if not table:
                result["error"] = "No results found on NGO Darpan"
                return result

            rows = table.find_all("tr")
            data = {}
            for row in rows:
                cells = row.find_all(["td", "th"])
                if len(cells) >= 2:
                    key = cells[0].get_text(strip=True).lower().replace(" ", "_")
                    val = cells[1].get_text(strip=True)
                    data[key] = val

            if data:
                result["details"] = data
            else:
                result["error"] = "No data parsed from NGO Darpan"

    except httpx.RequestError as e:
        result["error"] = f"Network error: {str(e)}"
    except Exception as e:
        result["error"] = f"Scraping error: {str(e)}"

    return result
