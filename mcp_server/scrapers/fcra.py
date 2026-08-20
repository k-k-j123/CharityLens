import httpx
from bs4 import BeautifulSoup
from typing import Optional
import asyncio
import re

FCRA_SEARCH_URL = "https://fcraonline.nic.in/FCRA/public/viewForeignContribution/pekxForeignContDetailByRegistrationNumber.php"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]


async def check_fcra_status(
    registration_number: Optional[str] = None,
    ngo_name: Optional[str] = None,
    state: Optional[str] = None,
) -> dict:
    """Check FCRA registration status from the FCRA portal.

    Tries to scrape fcraonline.nic.in for registration details.
    Returns a dict with status info or an error message.
    """
    result = {
        "source": "fcraonline.nic.in",
        "registration_number": registration_number,
        "ngo_name": ngo_name,
        "registered": None,
        "status": None,
        "expiry_date": None,
        "fetch_method": "scrape",
        "error": None,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            headers = {"User-Agent": USER_AGENTS[0]}

            if registration_number:
                resp = await client.get(
                    FCRA_SEARCH_URL,
                    params={"RegNo": registration_number},
                    headers=headers,
                )
            elif ngo_name:
                search_url = "https://fcraonline.nic.in/FCRA/public/viewForeignContribution/pekxForeignContDetailByName.php"
                resp = await client.get(
                    search_url,
                    params={"Name": ngo_name, "State": state or ""},
                    headers=headers,
                )
            else:
                result["error"] = "Provide either registration_number or ngo_name"
                return result

            if resp.status_code != 200:
                result["error"] = f"HTTP {resp.status_code} from FCRA portal"
                return result

            soup = BeautifulSoup(resp.text, "html.parser")
            table = soup.find("table", {"class": "table"})

            if not table:
                result["error"] = "No results found on FCRA portal"
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
                result["registered"] = True
                result["status"] = data.get("status", data.get("registration_status", "unknown"))
                result["expiry_date"] = data.get("valid_upto", data.get("expiry_date"))
                result["raw_data"] = data
            else:
                result["registered"] = False
                result["status"] = "not_found"

    except httpx.RequestError as e:
        result["error"] = f"Network error: {str(e)}"
    except Exception as e:
        result["error"] = f"Scraping error: {str(e)}"

    return result
