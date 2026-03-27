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

SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")

AUDIO_DIR = os.path.join(os.path.dirname(__file__), "audio")
