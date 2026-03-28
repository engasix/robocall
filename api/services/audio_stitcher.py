import os
import config
from pydub import AudioSegment

from api.services.tts import get_greeting_audio, get_store_segment_path, get_amount_audio, get_static_path
from api.services.name_utils import extract_first_name

CALLS_DIR = os.path.join(config.AUDIO_DIR, "calls")

PAUSE_SHORT  = AudioSegment.silent(duration=300)   # between greeting and store sentence
PAUSE_MEDIUM = AudioSegment.silent(duration=500)   # between sentences


def _load(path: str) -> AudioSegment:
    return AudioSegment.from_mp3(path)


def build_call_audio(
    order_id: int,
    customer_name: str,
    store_id: int,
    store_name: str,
    order_amount: float,
    language: str,
) -> str:
    """
    Stitch all segments into a single call script MP3.

    Flow (both languages):
      [greeting + name]  +  [store sentence]  +  [amount]  +  [key prompt]

    Urdu example:
      "Assalam o Alikum Asif"
      "Urdu Scents per order place karny ka sukriya, aapka order amount hay"
      "1500"
      'Order confirm karny k lye "1" dabaen ya order cancel karny k lye "2" daben.'

    English example:
      "Hello Asif"
      "Thanks for placing order on English Scents, your order amount is"
      "1,500"
      'To confirm your order press "1" or for cancellation press "2".'
    """
    first_name = extract_first_name(customer_name)

    greeting     = _load(get_greeting_audio(first_name, language))
    store_seg    = _load(get_store_segment_path(store_id, language))
    amount_audio = _load(get_amount_audio(order_amount, language))
    key_prompt   = _load(get_static_path("key_prompt", language))

    stitched = (
        greeting     + PAUSE_SHORT  +
        store_seg    + PAUSE_SHORT  +
        amount_audio + PAUSE_MEDIUM +
        key_prompt
    )

    os.makedirs(CALLS_DIR, exist_ok=True)
    output_path = os.path.join(CALLS_DIR, f"{order_id}.mp3")
    stitched.export(output_path, format="mp3", bitrate="128k")

    return output_path
