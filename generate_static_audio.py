"""
Regenerate static and per-store audio segments (skips already-generated files).
Run this only when you need to add new static segments or onboard new stores.

Usage:
    uv run generate_static_audio.py           # Generate missing files only
    uv run generate_static_audio.py --fresh   # Delete all audio first, then regenerate
"""

import os
import sys
import shutil
import config
from database import SessionLocal, Store
from api.services.tts import generate_static_segments, generate_store_segment

AUDIO_SUBDIRS = [
    "static/english", "static/urdu",
    "stores",
    "names/english", "names/urdu",
    "amounts/english", "amounts/urdu",
    "calls",
]


def clear_all_audio() -> None:
    print("Clearing all audio files...\n")
    for subdir in AUDIO_SUBDIRS:
        path = os.path.join(config.AUDIO_DIR, subdir)
        if os.path.exists(path):
            shutil.rmtree(path)
        os.makedirs(path)
        print(f"  [clear] audio/{subdir}/")


def generate_all_store_segments() -> None:
    db = SessionLocal()
    try:
        stores = db.query(Store).all()
        for store in stores:
            for language in ["urdu", "english"]:
                generate_store_segment(store.id, store.business_name, language)
    finally:
        db.close()


if __name__ == "__main__":
    clear_all_audio()
    print()    

    print("Generating shared static segments...\n")
    generate_static_segments()

    print("\nGenerating per-store sentences...\n")
    generate_all_store_segments()

    print("\nDone.")
