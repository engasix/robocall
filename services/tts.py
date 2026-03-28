import os
import config
from elevenlabs.client import ElevenLabs
from num2words import num2words

client = ElevenLabs(api_key=config.ELEVENLABS_API_KEY)

MODEL_ID = "eleven_multilingual_v2"
OUTPUT_FORMAT = "mp3_44100_128"

VOICE_IDS = {
    "urdu":    config.ELEVENLABS_VOICE_ID_URDU,
    "english": config.ELEVENLABS_VOICE_ID_ENGLISH,
}

# Shared static segments (same for all stores)
STATIC_SEGMENTS = {
    "english": {
        "key_prompt":  'To confirm your order press "1" or for cancellation press "2".',
        "confirmed":   "Thank you. Your order has been confirmed. Have a great day. Goodbye.",
        "cancelled":   "Understood. Your order has been cancelled. Thank you. Goodbye.",
        "no_response": "We did not receive your response. We will try again later. Goodbye.",
    },
    "urdu": {
        "key_prompt":  'آرڈر کنفرم کرنے کے لیے "1" دبائیں یا آرڈر کینسل کرنے کے لیے "2" دبائیں۔',
        "confirmed":   "شکریہ۔ آپ کا آرڈر کنفرم ہو گیا ہے۔ خدا حافظ۔",
        "cancelled":   "آپ کا آرڈر کینسل کر دیا گیا ہے۔ شکریہ۔ خدا حافظ۔",
        "no_response": "ہم نے آپ کا جواب نہیں ملا۔ ہم دوبارہ کوشش کریں گے۔ خدا حافظ۔",
    },
}

# Per-store sentence template (store name embedded at generation time)
STORE_SENTENCE = {
    "urdu":    "{store_name} پر آرڈر دینے کا شکریہ، آپ کے آرڈر کی رقم ہے",
    "english": "Thanks for placing order on {store_name}, your order amount is",
}

# Greeting template (first name embedded at generation time)
GREETING = {
    "urdu":    "السلام علیکم {first_name}",
    "english": "Hello {first_name}",
}


def _generate_audio(text: str, language: str, filepath: str) -> None:
    """Call ElevenLabs TTS and save audio to filepath."""
    voice_id = VOICE_IDS.get(language, VOICE_IDS["english"])
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    audio = client.text_to_speech.convert(
        voice_id=voice_id,
        text=text,
        model_id=MODEL_ID,
        output_format=OUTPUT_FORMAT,
    )
    with open(filepath, "wb") as f:
        for chunk in audio:
            if isinstance(chunk, bytes):
                f.write(chunk)


def generate_static_segments() -> None:
    """Generate shared static segments for both languages (skips existing files)."""
    for language, segments in STATIC_SEGMENTS.items():
        for key, text in segments.items():
            filepath = os.path.join(config.AUDIO_DIR, "static", language, f"{key}.mp3")
            if os.path.exists(filepath):
                print(f"  [skip]  static/{language}/{key}.mp3")
                continue
            print(f"  [gen]   static/{language}/{key}.mp3  →  \"{text}\"")
            _generate_audio(text, language, filepath)


def generate_store_segment(store_id: int, store_name: str, language: str) -> None:
    """Generate the per-store sentence for a given language."""
    text = STORE_SENTENCE[language].format(store_name=store_name)
    filepath = os.path.join(config.AUDIO_DIR, "stores", f"{store_id}_{language}.mp3")
    if os.path.exists(filepath):
        print(f"  [skip]  stores/{store_id}_{language}.mp3")
        return
    print(f"  [gen]   stores/{store_id}_{language}.mp3  →  \"{text}\"")
    _generate_audio(text, language, filepath)


def get_greeting_audio(first_name: str, language: str) -> str:
    """Return path to greeting audio for a customer name, generating if needed.
    e.g. 'Assalam o Alikum Asif' or 'Hello Asif'
    """
    text = GREETING[language].format(first_name=first_name)
    safe = first_name.lower().replace(" ", "_")
    filepath = os.path.join(config.AUDIO_DIR, "names", language, f"{safe}.mp3")
    if not os.path.exists(filepath):
        _generate_audio(text, language, filepath)
    return filepath


def get_store_segment_path(store_id: int, language: str) -> str:
    """Return path to the pre-generated store sentence."""
    return os.path.join(config.AUDIO_DIR, "stores", f"{store_id}_{language}.mp3")


def get_amount_audio(amount: float, language: str) -> str:
    """Return path to audio for an order amount, generating if needed."""
    amount_int = int(amount)
    text = _format_amount(amount_int, language)
    filepath = os.path.join(config.AUDIO_DIR, "amounts", language, f"{amount_int}.mp3")
    if not os.path.exists(filepath):
        _generate_audio(text, language, filepath)
    return filepath


def get_static_path(key: str, language: str) -> str:
    """Return path to a shared static segment."""
    return os.path.join(config.AUDIO_DIR, "static", language, f"{key}.mp3")


def _format_amount(amount: int, language: str) -> str:
    """Format a numeric amount into speakable text."""
    if language == "urdu":
        if amount >= 100_000:
            lakhs = amount // 100_000
            remainder = amount % 100_000
            return f"{lakhs} لاکھ {remainder}" if remainder else f"{lakhs} لاکھ"
        if amount >= 1_000:
            thousands = amount // 1_000
            remainder = amount % 1_000
            return f"{thousands} ہزار {remainder}" if remainder else f"{thousands} ہزار"
        return str(amount)
    return num2words(amount, lang="en")
