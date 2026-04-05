"""
Database management script — migrations and resets.

Commands:
    uv run manage_db.py migrate          # Create / update all tables
    uv run manage_db.py seed             # Insert demo stores (skips if already exist)
    uv run manage_db.py truncate         # Truncate orders, customer_names, order_amounts
    uv run manage_db.py truncate --all   # Truncate all tables including stores
    uv run manage_db.py drop             # Drop customer_names and order_amounts (schema change)
"""

import os
import sys
import shutil
import config
from sqlalchemy import text
from database import engine, init_db, SessionLocal, Store

def _add_column_if_missing(table: str, column: str, definition: str) -> None:
    """Add a column to a table only if it doesn't already exist."""
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT COUNT(*) FROM information_schema.columns "
            "WHERE table_schema = DATABASE() "
            "AND table_name = :table AND column_name = :column"
        ), {"table": table, "column": column})
        exists = result.scalar() > 0

    if exists:
        print(f"  [skip]  {table}.{column} already exists")
    else:
        with engine.connect() as conn:
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {definition}"))
            conn.commit()
        print(f"  [added] {table}.{column}")


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
    """Create all tables if they don't exist, then apply column migrations."""
    print("Running migrations...\n")
    init_db()
    print("  [done] All tables created / verified.")
    _add_column_if_missing("stores", "api_key_hash",       "VARCHAR(64) NULL")
    _add_column_if_missing("stores", "webhook_url",        "VARCHAR(500) NULL")
    _add_column_if_missing("stores", "timezone",           "VARCHAR(50) NOT NULL DEFAULT 'Asia/Karachi'")
    _add_column_if_missing("stores", "call_window_start",  "TIME NOT NULL DEFAULT '09:00:00'")
    _add_column_if_missing("stores", "call_window_end",    "TIME NOT NULL DEFAULT '21:00:00'")
    _add_column_if_missing("orders", "retry_count",        "INT NOT NULL DEFAULT 0")
    _add_column_if_missing("orders", "next_retry_at",      "DATETIME NULL")


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


DEMO_STORES = [
    {
        "business_name": "Urdu Scents",
        "email":         "ur@robocalls.ai",
        "phone":         "+923001092233",
        "language":      "urdu",
        "password_hash": "$2b$12$DEulLNjDL88aJ6KfYfvaReURT9oa/tK/1wtfEjaGVNorzxbPFp2MK",
    },
    {
        "business_name": "English Scents",
        "email":         "en@robocalls.ai",
        "phone":         "+923001092233",
        "language":      "english",
        "password_hash": "$2b$12$ESRS6KDtlyPXgRqBhk6Vy.USrc4EhH5dxzAcgA8Y.GIwjMmQyUnvO",
    },
]


def seed() -> None:
    """Insert demo stores — skips any store whose email already exists."""
    print("Seeding demo stores...\n")
    db = SessionLocal()
    try:
        for store_data in DEMO_STORES:
            exists = db.query(Store).filter(Store.email == store_data["email"]).first()
            if exists:
                print(f"  [skip]  {store_data['business_name']} (already exists)")
            else:
                db.add(Store(**store_data))
                db.commit()
                print(f"  [added] {store_data['business_name']}")
    finally:
        db.close()
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
    "migrate":  lambda args: migrate(),
    "seed":     lambda args: seed(),
    "truncate": lambda args: truncate(all_tables="--all" in args),
    "drop":     lambda args: drop(),
}

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0] not in COMMANDS:
        print(__doc__)
        sys.exit(1)
    COMMANDS[args[0]](args[1:])
