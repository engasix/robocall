"""
Run this script to fully reset and regenerate all audio.
- Deletes ALL audio files (names, amounts, calls, stores, static)
- Truncates all DB tables except stores
- Regenerates static segments and per-store sentences from scratch

Usage:
    uv run generate_static_audio.py
"""

import os
import shutil
import config
from sqlalchemy import text
from database import SessionLocal, Store, engine
from api.services.tts import generate_static_segments, generate_store_segment

AUDIO_SUBDIRS = ["static/english", "static/urdu", "stores", "names/english", "names/urdu",
                 "amounts/english", "amounts/urdu", "calls"]


def clear_all_audio() -> None:
    print("Clearing all audio files...\n")
    for subdir in AUDIO_SUBDIRS:
        path = os.path.join(config.AUDIO_DIR, subdir)
        if os.path.exists(path):
            shutil.rmtree(path)
        os.makedirs(path)
        print(f"  [clear] audio/{subdir}/")


def truncate_tables() -> None:
    print("\nTruncating database tables...\n")
    with engine.connect() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        for table in ["orders", "customer_names", "order_amounts"]:
            conn.execute(text(f"TRUNCATE TABLE {table}"))
            print(f"  [truncated] {table}")
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
        conn.commit()


def generate_all_store_segments() -> None:
    db = SessionLocal()
    try:
        stores = db.query(Store).all()
        for store in stores:
            generate_store_segment(store.id, store.business_name, store.language)
    finally:
        db.close()


if __name__ == "__main__":
    clear_all_audio()
    truncate_tables()

    print("\nGenerating shared static segments...\n")
    generate_static_segments()

    print("\nGenerating per-store sentences...\n")
    generate_all_store_segments()

    print("\nDone.")
