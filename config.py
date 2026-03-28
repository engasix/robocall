from dotenv import load_dotenv
import os

load_dotenv()

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID_URDU = os.getenv("ELEVENLABS_VOICE_ID_URDU")
ELEVENLABS_VOICE_ID_ENGLISH = os.getenv("ELEVENLABS_VOICE_ID_ENGLISH")

DATABASE_URL = os.getenv("DATABASE_URL")

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
API_URL  = os.getenv("API_URL",  "http://localhost:8001")

SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")

AUDIO_DIR = os.path.join(os.path.dirname(__file__), "audio")

# ── ElevenLabs Voice Settings ─────────────────────────────────────────────────
# speed:            0.7 (slow) → 1.2 (fast)       | default: 1.0
# stability:        0.0 (expressive) → 1.0 (monotone) | default: 0.5
# similarity_boost: 0.0 → 1.0 (closer to original voice)  | default: 0.75
# style:            0.0 → 1.0 (amplifies speaker style)    | default: 0.0
# use_speaker_boost: True / False (better similarity, adds latency)

VOICE_SETTINGS_URDU = {
    "speed":            0.85,
    "stability":        0.85,  # high = consistent pitch across chunks
    "similarity_boost": 0.90,  # high = locked to original voice tone
    "style":            0.0,
    "use_speaker_boost": True,
}

VOICE_SETTINGS_ENGLISH = {
    "speed":            0.85,
    "stability":        0.85,
    "similarity_boost": 0.90,
    "style":            0.0,
    "use_speaker_boost": True,
}
