"""
Medicines seeding helper for Dawaa'i AI.

main.py calls seed_initial_medicines() on startup. It is safe to call many
times: it only seeds when the `medicines` table has fewer than MIN_MEDICINES rows.
"""
import sqlite3

from app.config import settings
from app.database import get_connection

# Same threshold used by app/seed_extended.py
MIN_MEDICINES = 500


def seed_initial_medicines() -> None:
    conn = get_connection()
    try:
        try:
            count = conn.execute("SELECT COUNT(*) FROM medicines").fetchone()[0]
        except sqlite3.OperationalError:
            # table not created yet (init_db() creates it)
            return
    finally:
        conn.close()

    if count >= MIN_MEDICINES:
        return

    try:
        from app.seed_extended import seed_database_extended
        seed_database_extended(db_path=str(settings.DATABASE_PATH), force=False)
    except Exception as exc:
        print(f"[seed] could not seed medicines: {exc}")
