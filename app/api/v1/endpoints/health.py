import os
import sqlite3

from fastapi import APIRouter

router = APIRouter()


@router.get("/health", summary="Health check")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "ok"}


@router.get("/health/db", summary="DB health check")
async def health_db_check():
    """Check whether annotations.db is available and readable."""
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
    db_path = os.getenv("DB_PATH") or os.path.join(project_root, "database", "annotations.db")

    if not os.path.exists(db_path):
        return {"status": "error", "reason": "db_not_found"}

    table_samples = {}

    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            conn.execute("SELECT 1")

            tables = conn.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                  AND name NOT LIKE 'sqlite_%'
                ORDER BY name
                """
            ).fetchall()

            for table in tables:
                table_name = table["name"]
                safe_table = table_name.replace('"', '""')
                row = conn.execute(f'SELECT * FROM "{safe_table}" LIMIT 1').fetchone()
                table_samples[table_name] = dict(row) if row is not None else None
    except sqlite3.Error:
        return {"status": "error", "reason": "db_unreadable"}

    return {
        "status": "ok",
        "table_samples": table_samples,
    }
