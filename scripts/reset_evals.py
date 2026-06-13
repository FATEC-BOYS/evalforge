#!/usr/bin/env python3
"""
Deletes all rows from evaluations and audit_logs tables.
Users are preserved. Run with:
  docker compose exec api python scripts/reset_evals.py
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "evalforge"))

from sqlalchemy import text
from db.session import get_writer_session


async def reset() -> None:
    async with get_writer_session() as session:
        result_evals = await session.execute(text("DELETE FROM evaluations"))
        result_logs = await session.execute(text("DELETE FROM audit_logs"))
        print(f"Deleted {result_evals.rowcount} evaluations")
        print(f"Deleted {result_logs.rowcount} audit log entries")


if __name__ == "__main__":
    asyncio.run(reset())
