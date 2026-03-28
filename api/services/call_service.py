import config
from twilio.rest import Client

client = Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)


def trigger_call(order_id: int, phone: str) -> str:
    """Initiate an outbound Twilio call for the given order.

    Plays the stitched call audio and gathers a single keypress from the customer.
    Returns the Twilio call SID.
    """
    audio_url = f"{config.API_URL}/audio/calls/{order_id}.mp3"
    webhook_url = f"{config.API_URL}/webhook/keypress/{order_id}"
    status_url = f"{config.API_URL}/webhook/call-status/{order_id}"

    call = client.calls.create(
        to=phone,
        from_=config.TWILIO_PHONE_NUMBER,
        twiml=f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Gather numDigits="1" action="{webhook_url}" method="POST" timeout="10">
        <Play>{audio_url}</Play>
    </Gather>
    <Redirect method="POST">{webhook_url}</Redirect>
</Response>""",
        status_callback=status_url,
        status_callback_method="POST",
    )

    return call.sid
