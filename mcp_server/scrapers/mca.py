import httpx
from bs4 import BeautifulSoup
from typing import Optional

MCA_SEARCH_URL = "https://www.mca.gov.in/content/mca/global/en/data-and-reports/section-8company.html"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]


async def get_mca_filings(
    company_name: Optional[str] = None,
    cin: Optional[str] = None,
) -> dict:
    """Fetch Section 8 company filings from MCA portal.

    Looks for AOC-4 (financial statements) and MGT-7 (annual returns).
    Returns filing dates and availability.
    """
    result = {
        "source": "mca.gov.in",
        "company_name": company_name,
        "cin": cin,
        "filings": [],
        "latest_filing_date": None,
        "fetch_method": "scrape",
        "error": None,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            headers = {"User-Agent": USER_AGENTS[0]}

            if cin:
                search_url = f"https://www.mca.gov.in/content/mca/global/en/data-and-reports/section-8company/search.html"
                resp = await client.get(
                    search_url,
                    params={"cin": cin},
                    headers=headers,
                )
            elif company_name:
                search_url = f"https://www.mca.gov.in/content/mca/global/en/data-and-reports/section-8company/search.html"
                resp = await client.get(
                    search_url,
                    params={"company_name": company_name},
                    headers=headers,
                )
            else:
                result["error"] = "Provide either CIN or company_name"
                return result

            if resp.status_code != 200:
                result["error"] = f"HTTP {resp.status_code} from MCA portal"
                return result

            soup = BeautifulSoup(resp.text, "html.parser")
            table = soup.find("table", {"class": "table"})

            if not table:
                result["error"] = "No results found on MCA portal"
                return result

            rows = table.find_all("tr")
            filings = []
            for row in rows[1:]:
                cells = row.find_all("td")
                if len(cells) >= 3:
                    filing = {
                        "form_type": cells[0].get_text(strip=True),
                        "filing_date": cells[1].get_text(strip=True),
                        "description": cells[2].get_text(strip=True),
                    }
                    filings.append(filing)

            if filings:
                result["filings"] = filings
                dates = [f["filing_date"] for f in filings if f["filing_date"]]
                if dates:
                    result["latest_filing_date"] = max(dates)
            else:
                result["error"] = "No filings found"

    except httpx.RequestError as e:
        result["error"] = f"Network error: {str(e)}"
    except Exception as e:
        result["error"] = f"Scraping error: {str(e)}"

    return result
