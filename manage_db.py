"""
Database management script — migrations and resets.

Commands:
    uv run manage_db.py migrate          # Create / update all tables
    uv run manage_db.py truncate         # Truncate orders, customer_names, order_amounts
    uv run manage_db.py truncate --all   # Truncate all tables including stores
    uv run manage_db.py drop             # Drop customer_names and order_amounts (schema change)
"""

import os
import sys
import shutil
import config
from sqlalchemy import text
from database import engine, init_db

AUDIO_CACHE_DIRS = [
    "amounts/urdu", "amounts/english",
    "names/urdu", "names/english",
    "calls",
]


def clear_audio_cache() -> None:
    print("Clearing cached audio files...\n")
    for subdir in AUDIO_CACHE_DIRS:
        path = os.path.join(config.AUDIO_DIR, subdir)
        if os.path.exists(path):
            shutil.rmtree(path)
        os.makedirs(path)
        print(f"  [clear] audio/{subdir}/")


def migrate() -> None:
    """Create all tables if they don't exist (safe to run multiple times)."""
    print("Running migrations...\n")
    init_db()
    print("  [done] All tables created / verified.")


def truncate(all_tables: bool = False) -> None:
    tables = ["orders", "customer_names", "order_amounts"]
    if all_tables:
        tables.append("stores")

    print(f"Truncating tables: {', '.join(tables)}\n")
    with engine.connect() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        for table in tables:
            conn.execute(text(f"TRUNCATE TABLE {table}"))
            print(f"  [truncated] {table}")
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
        conn.commit()

    print()
    clear_audio_cache()
    print("\nDone.")


def drop() -> None:
    """Drop and recreate customer_names and order_amounts (use after schema changes)."""
    print("Dropping customer_names and order_amounts...\n")
    with engine.connect() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        conn.execute(text("DROP TABLE IF EXISTS customer_names"))
        conn.execute(text("DROP TABLE IF EXISTS order_amounts"))
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
        conn.commit()
    print("  [dropped] customer_names, order_amounts")
    migrate()


COMMANDS = {
    "migrate": lambda args: migrate(),
    "truncate": lambda args: truncate(all_tables="--all" in args),
    "drop": lambda args: drop(),
}

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0] not in COMMANDS:
        print(__doc__)
        sys.exit(1)
    COMMANDS[args[0]](args[1:])
