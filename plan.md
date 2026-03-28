# Robocall Order Confirmation System — Implementation Plan

## Overview
A demo system where a customer places a COD order on a webpage, and an AI voice agent automatically calls them for order confirmation using pre-generated ElevenLabs audio stitched together at runtime.

---

## Tech Stack

| Layer | Tool |
|---|---|
| Frontend | HTML + Tailwind CSS |
| Backend | Python + FastAPI |
| Outbound Calling | Twilio (demo) → Local SIP (production) |
| TTS / Voice | ElevenLabs API |
| Audio Stitching | pydub (Python) |
| Database | MySQL + SQLAlchemy |
| Audio Storage | Local filesystem (demo) → S3 (production) |

---

## Project Structure

```
robocall/
├── main.py                   # FastAPI app entry point
├── config.py                 # Environment variables & settings
├── database.py               # MySQL models & connection
├── generate_static_audio.py  # One-time script: clears audio, truncates DB, regenerates static
├── requirements.txt
├── .env                      # API keys (Twilio, ElevenLabs)
├── plan.md
│
├── routers/
│   ├── orders.py             # POST /place-order, GET /api/orders
│   └── auth.py               # GET/POST /login, GET /logout
│
├── services/
│   ├── tts.py                # ElevenLabs TTS generation & caching
│   ├── audio_stitcher.py     # Audio stitching with pydub
│   ├── name_utils.py         # Pakistani name extraction logic
│   └── call_service.py       # Twilio outbound call trigger (Phase 5)
│
├── audio/
│   ├── static/
│   │   ├── urdu/             # key_prompt, confirmed, cancelled, no_response
│   │   └── english/          # key_prompt, confirmed, cancelled, no_response
│   ├── stores/               # Per-store sentence audio (store_id_language.mp3)
│   ├── names/
│   │   ├── urdu/             # Cached greeting+name audio per customer
│   │   └── english/
│   ├── amounts/
│   │   ├── urdu/             # Cached amount audio (amount.mp3)
│   │   └── english/
│   └── calls/                # Final stitched call audio per order (order_id.mp3)
│
├── static/css/
│   ├── input.css             # Tailwind v4 source
│   └── style.css             # Compiled output
│
└── templates/
    ├── login.html            # Store login page
    ├── index.html            # Order placement form
    └── dashboard.html        # Live order status dashboard
```

---

## Implementation Phases

### Phase 1 — Project Setup ✅
- [x] Initialize FastAPI project
- [x] Setup `.env` with Twilio & ElevenLabs credentials
- [x] Setup MySQL database with `stores`, `orders`, `customer_names` and `order_amounts` tables
- [x] Install dependencies: `fastapi`, `uvicorn`, `twilio`, `pydub`, `elevenlabs`, `sqlalchemy`, `pymysql`, `python-dotenv`, `num2words`
- [x] Migrated to `uv` for package management (`pyproject.toml` as source of truth)

**stores Table Schema:**
```
id, business_name, email, phone, language (enum: urdu, english), password_hash, created_at, updated_at
```

**Orders Table Schema:**
```
id, store_id (FK → stores), customer_name, phone, order_amount, status (pending/confirmed/cancelled/no_response), created_at, updated_at
```

---

### Phase 2 — Frontend (Order Form + Dashboard) ✅
- [x] Build `login.html` — store authentication page
- [x] Build `index.html` — order placement form
  - Fields: Customer Name, Phone Number (with country flag picker via intl-tel-input), Store, Order Amount
  - Async submit: POST to `/place-order`, show success/error banner
- [x] Build `dashboard.html` — live order status table
  - Columns: Order ID, Customer Name, Phone, Store, Amount, Status, Time
  - Stats row: Total / Pending / Confirmed / Cancelled counts
  - Auto-refresh every 5 seconds
- [x] Tailwind CSS v4 with warm charcoal (`#33302B`) color theme
- [x] All styles in `input.css` — zero inline styles in HTML templates

---

### Phase 3 — TTS Audio Setup ✅
- [x] Write `services/tts.py` to call ElevenLabs API (`eleven_multilingual_v2` model)
- [x] Generate shared static segments in both languages:
  - `audio/static/urdu/` — key_prompt, confirmed, cancelled, no_response (proper Urdu script)
  - `audio/static/english/` — same segments in English
- [x] Per-store sentence audio generated at setup time:
  - Urdu: `"{store_name} پر آرڈر دینے کا شکریہ، آپ کے آرڈر کی رقم ہے"`
  - English: `"Thanks for placing order on {store_name}, your order amount is"`
- [x] Greeting + name as single TTS call (cached per first name):
  - Urdu: `"السلام علیکم {first_name}"`
  - English: `"Hello {first_name}"`
- [x] Amount audio cached per unique amount using `num2words` for English, Urdu script words for Urdu
- [x] `generate_static_audio.py` — full reset script: clears all audio, truncates DB tables, regenerates static + store sentences

---

### Phase 4 — Audio Stitching Service ✅
- [x] Write `services/audio_stitcher.py` using `pydub`
- [x] `build_call_audio(order_id, customer_name, store_id, store_name, order_amount, language)`:
  1. Generate/retrieve greeting+name audio (cached per first name)
  2. Load pre-generated store sentence
  3. Generate/retrieve amount audio (cached per amount)
  4. Load shared key_prompt static segment
  5. Concatenate with natural pauses → export as `audio/calls/{order_id}.mp3`
- [x] Stitching triggered as FastAPI `BackgroundTask` on order placement (returns instantly to user)

**Call Script Flow:**
```
[greeting + name]  →  [store sentence]  →  [amount]  →  [key prompt]

Urdu:    "السلام علیکم Asif" | "Urdu Scents پر آرڈر دینے کا شکریہ..." | "ڈیڑھ ہزار" | "1 دبائیں یا 2..."
English: "Hello Asif" | "Thanks for placing order on English Scents..." | "one thousand, five hundred" | "Press 1 or 2..."
```

---

### Phase 5 — Calling Service (Twilio Integration)
- [ ] Write `services/call_service.py`
- [ ] `trigger_call(order_id, phone)`:
  - Serve stitched MP3 via public URL
  - Initiate Twilio outbound call with TwiML:
    ```xml
    <Response>
      <Play>https://yourdomain.com/audio/calls/{order_id}.mp3</Play>
      <Gather numDigits="1" action="/webhook/keypress/{order_id}" />
    </Response>
    ```
- [ ] Wire `trigger_call()` into `process_order()` background task after `build_call_audio()`

---

### Phase 6 — Twilio Webhooks
- [ ] `POST /webhook/keypress/{order_id}` — handle digit press:
  - Digit `1` → status: `confirmed` → play `confirmed.mp3`
  - Digit `2` → status: `cancelled` → play `cancelled.mp3`
  - No input → status: `no_response` → play `no_response.mp3`
- [ ] `POST /webhook/call-status/{order_id}` — handle call events (failed, busy, no-answer)

---

### Phase 7 — Order Placement Endpoint ✅
- [x] `POST /place-order` — saves order, returns instantly, triggers background task
- [x] `GET /api/orders` — returns all orders for dashboard (filter by store ready for future)
- [x] Background task: `build_call_audio()` → TODO: `trigger_call()` (Phase 5)

---

### Phase 8 — Dashboard & Polish (partial)
- [x] Live order status dashboard with 5s polling
- [x] Status badges: pending=amber, confirmed=green, cancelled=red, no_response=gray
- [ ] Clean up temp call audio files after call ends
- [ ] End-to-end testing

---

## Call Flow Summary

```
Customer places order on webpage
        │
        ▼
Backend saves order (status: pending) → responds instantly
        │
        ▼
Background task:
  1. Stitch audio: greeting+name → store sentence → amount → key prompt
  2. Trigger Twilio outbound call (Phase 5)
        │
        ▼
Customer phone rings → answers
        │
        ▼
Audio plays (personalized message)
        │
        ├── Presses 1 → confirmed.mp3 → status: confirmed
        ├── Presses 2 → cancelled.mp3 → status: cancelled
        └── No response → no_response.mp3 → status: no_response
        │
        ▼
Dashboard updates live
```

---

## API Keys Required

| Service | Purpose |
|---|---|
| Twilio Account SID | Outbound calling |
| Twilio Auth Token | Outbound calling |
| Twilio Phone Number | Caller ID |
| ElevenLabs API Key | TTS generation |
| ElevenLabs Voice ID (Urdu) | Urdu voice |
| ElevenLabs Voice ID (English) | English voice |

---

## Production Migration (Post-Demo)

| Demo | Production |
|---|---|
| Twilio calling | Local Pakistani SIP trunk |
| Local audio files | AWS S3 |
| MySQL | MySQL (same, scale vertically) |
| Single server | Dockerized + hosted |

---

## Cost Per Call (Production Estimate)

| Item | Cost (PKR) |
|---|---|
| SIP call ~45 sec | ~2.00 |
| ElevenLabs (amortized, name cache) | ~0.15 |
| Server infra | ~0.50 |
| **Total** | **~PKR 2.65** |
| **Sell at** | **PKR 6.00** |
| **Margin** | **~55%** |
