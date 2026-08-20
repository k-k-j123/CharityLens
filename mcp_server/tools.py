import sqlite3
import os
from typing import Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "ngos.db")


def _get_conn(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _row_to_dict(row: sqlite3.Row) -> dict:
    return dict(row)


async def search_ngo_by_name(name: str, limit: int = 10, db_path: str = DB_PATH) -> dict:
    conn = _get_conn(db_path)
    try:
        cursor = conn.execute(
            "SELECT rowid, * FROM ngos WHERE rowid IN "
            "(SELECT rowid FROM ngos_fts WHERE ngos_fts MATCH ?) "
            "LIMIT ?",
            (f'"{name}"*', limit),
        )
        rows = cursor.fetchall()
        results = [_row_to_dict(r) for r in rows]

        if not results:
            cursor = conn.execute(
                "SELECT rowid, * FROM ngos WHERE name LIKE ? LIMIT ?",
                (f"%{name}%", limit),
            )
            rows = cursor.fetchall()
            results = [_row_to_dict(r) for r in rows]

        return {"results": results, "total": len(results), "query": name}
    finally:
        conn.close()


async def get_ngo_by_id(ngo_id: int, db_path: str = DB_PATH) -> dict:
    conn = _get_conn(db_path)
    try:
        cursor = conn.execute("SELECT rowid, * FROM ngos WHERE rowid = ?", (ngo_id,))
        row = cursor.fetchone()
        if row:
            return {"ngo": _row_to_dict(row), "found": True}
        return {"ngo": None, "found": False, "error": f"NGO with id {ngo_id} not found"}
    finally:
        conn.close()


async def list_ngos_by_state(
    state: str, limit: int = 50, offset: int = 0, db_path: str = DB_PATH
) -> dict:
    conn = _get_conn(db_path)
    try:
        cursor = conn.execute(
            "SELECT rowid, * FROM ngos WHERE LOWER(state) = LOWER(?) "
            "LIMIT ? OFFSET ?",
            (state, limit, offset),
        )
        rows = cursor.fetchall()
        results = [_row_to_dict(r) for r in rows]

        count_cursor = conn.execute(
            "SELECT COUNT(*) FROM ngos WHERE LOWER(state) = LOWER(?", (state,)
        )
        total = count_cursor.fetchone()[0]

        return {"results": results, "total": total, "state": state, "limit": limit, "offset": offset}
    finally:
        conn.close()


async def get_ngo_stats(db_path: str = DB_PATH) -> dict:
    conn = _get_conn(db_path)
    try:
        total = conn.execute("SELECT COUNT(*) FROM ngos").fetchone()[0]
        states = conn.execute(
            "SELECT state, COUNT(*) as count FROM ngos GROUP BY state ORDER BY count DESC"
        ).fetchall()

        return {
            "total_ngos": total,
            "states": [{"state": r["state"], "count": r["count"]} for r in states],
        }
    finally:
        conn.close()


async def check_fcra_status(
    registration_number: Optional[str] = None,
    ngo_name: Optional[str] = None,
    state: Optional[str] = None,
) -> dict:
    from mcp_server.scrapers.fcra import check_fcra_status as _scrape_fcra
    return await _scrape_fcra(
        registration_number=registration_number,
        ngo_name=ngo_name,
        state=state,
    )


async def get_ngo_darpan_details(
    ngo_name: Optional[str] = None,
    state: Optional[str] = None,
    registration_number: Optional[str] = None,
) -> dict:
    from mcp_server.scrapers.ngo_darpan import get_ngo_darpan_details as _scrape_darpan
    return await _scrape_darpan(
        ngo_name=ngo_name,
        state=state,
        registration_number=registration_number,
    )


async def get_mca_filings(
    company_name: Optional[str] = None,
    cin: Optional[str] = None,
) -> dict:
    from mcp_server.scrapers.mca import get_mca_filings as _scrape_mca
    return await _scrape_mca(company_name=company_name, cin=cin)


async def search_adverse_media(
    ngo_name: str, state: Optional[str] = None, max_results: int = 5
) -> dict:
    from mcp_server.scrapers.news import search_adverse_media as _scrape_news
    return await _scrape_news(ngo_name=ngo_name, state=state, max_results=max_results)


TOOL_REGISTRY = {
    "search_ngo_by_name": search_ngo_by_name,
    "get_ngo_by_id": get_ngo_by_id,
    "list_ngos_by_state": list_ngos_by_state,
    "get_ngo_stats": get_ngo_stats,
    "check_fcra_status": check_fcra_status,
    "get_ngo_darpan_details": get_ngo_darpan_details,
    "get_mca_filings": get_mca_filings,
    "search_adverse_media": search_adverse_media,
}
