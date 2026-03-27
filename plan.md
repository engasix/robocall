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
├── main.py                  # FastAPI app entry point
├── config.py                # Environment variables & settings
├── database.py              # MySQL models & connection
├── requirements.txt
├── .env                     # API keys (Twilio, ElevenLabs)
├── plan.md
│
├── routers/
│   ├── orders.py            # POST /place-order endpoint
│   ├── calls.py             # Twilio webhook endpoints
│   └── dashboard.py         # GET /dashboard endpoint
│
├── services/
│   ├── tts_service.py       # ElevenLabs TTS generation & caching
│   ├── audio_service.py     # Audio stitching with pydub
│   └── call_service.py      # Twilio outbound call trigger
│
├── audio/
│   ├── static/
│   │   ├── urdu/                # Static segments in Urdu
│   │   │   ├── greeting.mp3         # "Assalam o Alaikum"
│   │   │   ├── store_connector.mp3  # "per order place karny ka shukriya"
│   │   │   ├── amount_prefix.mp3    # "aapka order amount hay"
│   │   │   ├── instructions.mp3     # "order confirm karny k lye 1 dabaen, cancel k lye 2 dabaen"
│   │   │   ├── thankyou.mp3         # "order confirm karny ka shukriya"
│   │   │   └── cancelled.mp3        # "aapka order cancel kar diya gaya"
│   │   │
│   │   └── english/             # Static segments in English
│   │       ├── greeting.mp3         # "Hello"
│   │       ├── store_connector.mp3  # "thank you for placing an order at"
│   │       ├── amount_prefix.mp3    # "your order amount is"
│   │       ├── instructions.mp3     # "press 1 to confirm or press 2 to cancel"
│   │       ├── thankyou.mp3         # "thank you for confirming your order"
│   │       └── cancelled.mp3        # "your order has been cancelled"
│   │
│   ├── amounts/
│   │   ├── urdu/                # Cached amounts in Urdu, filename = DB record id
│   │   │   └── 1.mp3, 2.mp3, 3.mp3 ...
│   │   └── english/             # Cached amounts in English, filename = DB record id
│   │       └── 1.mp3, 2.mp3, 3.mp3 ...
│   │
│   ├── stores/
│   │   ├── urdu/                # Store name audio in Urdu voice
│   │   │   └── <store_id>.mp3
│   │   └── english/             # Store name audio in English voice
│   │       └── <store_id>.mp3
│   │
│   ├── names/
│   │   ├── urdu/                # Customer name audio in Urdu voice
│   │   │   └── 1.mp3, 2.mp3, 3.mp3 ...
│   │   └── english/             # Customer name audio in English voice
│   │       └── 1.mp3, 2.mp3, 3.mp3 ...
│   │
│   └── calls/                   # Final stitched audio per call (temp, cleaned up after)
│       └── call_<order_id>.mp3
│
└── templates/
    ├── index.html           # Order placement form
    └── dashboard.html       # Live order status dashboard
```

---

## Implementation Phases

### Phase 1 — Project Setup ✅
- [x] Initialize FastAPI project
- [x] Setup `.env` with Twilio & ElevenLabs credentials
- [x] Setup MySQL database with `stores`, `orders`, `customer_names` and `order_amounts` tables
- [x] Install dependencies: `fastapi`, `uvicorn`, `twilio`, `pydub`, `elevenlabs`, `sqlalchemy`, `pymysql`, `python-dotenv`, `nameparser`
- [x] Migrated to `uv` for package management (`pyproject.toml` as source of truth)

**stores Table Schema:**
```
id, business_name, email, phone, language (enum: urdu, english), created_at, updated_at
```
- `language` — chosen by the store at onboarding, applies to all their calls
- All audio generation and stitching for this store's orders uses the selected language

**Orders Table Schema:**
```
id, store_id (FK → stores), customer_name, phone, order_amount, status (pending/confirmed/cancelled/no_response), created_at, updated_at
```

**customer_names Table Schema:**
```
id, full_name, first_name, created_at
```
- `full_name` — full name as entered by customer (e.g. "Syed Farish Hussain")
- `first_name` — extracted actual name using `nameparser` (e.g. "Farish")
- Audio file is stored as `audio/names/<id>.mp3` — no path needed in DB, derived from `id`

**order_amounts Table Schema:**
```
id, amount, created_at
```
- `amount` — order amount as a number (e.g. 1500)
- Audio file is stored as `audio/amounts/<id>.mp3` — derived from `id`

**Name Resolution Logic (used in tts_service.py):**
```
1. Extract first_name from full_name using nameparser
2. Check customer_names table: does first_name already exist?
   ├── YES → return audio/names/<id>.mp3 (no ElevenLabs call)
   └── NO  → insert record → call ElevenLabs → save as audio/names/<id>.mp3
```

**Amount Resolution Logic (used in tts_service.py):**
```
1. Check order_amounts table: does this amount already exist?
   ├── YES → return audio/amounts/<id>.mp3 (no ElevenLabs call)
   └── NO  → insert record → call ElevenLabs → save as audio/amounts/<id>.mp3
```

---

### Phase 2 — Frontend (Order Form + Dashboard) ✅
- [x] Build `index.html` — order placement form
  - Fields: Customer Name, Phone Number (with country flag picker via intl-tel-input), Store, Order Amount
  - On submit: POST to `/place-order`, show "You will receive a call shortly"
- [x] Build `dashboard.html` — live order status table
  - Columns: Order ID, Customer Name, Phone, Store, Amount, Status, Time
  - Stats row: Total / Pending / Confirmed / Cancelled counts
  - Auto-refresh every 5 seconds to show live status updates

---

### Phase 3 — TTS Audio Setup (One-Time Generation)
- [ ] Write `tts_service.py` to call ElevenLabs API
- [ ] Generate and save all **static segments** in both languages:
  - `audio/static/urdu/` — greeting, store_connector, amount_prefix, instructions, thankyou, cancelled
  - `audio/static/english/` — same segments in English
  - Use separate ElevenLabs voice IDs per language (Urdu voice vs English voice)
- [ ] Write **store name caching** logic: on store onboarding, generate audio for both languages — `audio/stores/urdu/<id>.mp3` and `audio/stores/english/<id>.mp3`
- [ ] Write **customer name resolution** logic:
  - Use `nameparser` + custom Pakistani honorifics (Syed, Muhammad, Mohammad, Abdul, Hafiz) to extract actual first name
  - Lookup `first_name` in `customer_names` table
  - If found → reuse `audio/names/<language>/<id>.mp3`
  - If not found → generate in both languages via ElevenLabs → save both → insert into `customer_names` table
- [ ] Write **amount resolution** logic:
  - Lookup `amount` in `order_amounts` table
  - If found → reuse `audio/amounts/<language>/<id>.mp3`
  - If not found → generate in both languages via ElevenLabs → save both → insert into `order_amounts` table

---

### Phase 4 — Audio Stitching Service
- [ ] Write `audio_service.py` using `pydub`
- [ ] `build_call_audio(order, language)` function — language derived from `client.language`:
  1. Load `static/<language>/greeting.mp3`
  2. Load `names/<language>/<id>.mp3` (from cache or generate)
  3. Load `stores/<language>/<store_id>.mp3` (from cache or generate)
  4. Load `static/<language>/store_connector.mp3`
  5. Load `static/<language>/amount_prefix.mp3`
  6. Load `amounts/<language>/<id>.mp3` (from cache or generate)
  7. Load `static/<language>/instructions.mp3`
  8. Concatenate all → export as `audio/calls/call_<order_id>.mp3`
- [ ] Add short silence (300ms) between segments for natural pacing

---

### Phase 5 — Calling Service (Twilio Integration)
- [ ] Write `call_service.py`
- [ ] `trigger_call(order)`:
  - Call `build_call_audio(order)` to stitch final mp3
  - Serve mp3 via a public URL (FastAPI static file endpoint)
  - Initiate Twilio outbound call with TwiML:
    ```xml
    <Response>
      <Play>https://yourdomain.com/audio/calls/call_<id>.mp3</Play>
      <Gather numDigits="1" action="/webhook/keypress/<order_id>">
      </Gather>
    </Response>
    ```
- [ ] Expose `/audio/calls/{filename}` as a static file route

---

### Phase 6 — Twilio Webhooks
- [ ] `POST /webhook/keypress/{order_id}` — handle digit press
  - Digit `1` → update order status to `confirmed` → play `thankyou.mp3` → hang up
  - Digit `2` → update order status to `cancelled` → play `cancelled.mp3` → hang up
  - No input → update status to `no_response`
- [ ] `POST /webhook/call-status/{order_id}` — handle call events (failed, busy, no-answer)

---

### Phase 7 — Order Placement Endpoint (partial)
- [x] `POST /place-order`:
  1. Validate input
  2. Save order to DB with status `pending`
  3. Return order confirmation to frontend
- [ ] Trigger `call_service.trigger_call(order)` asynchronously (background task) — pending Phase 5

---

### Phase 8 — Dashboard & Polish (partial)
- [x] Wire up dashboard with live status (`GET /api/orders` polled every 5s)
- [x] Add status color coding (pending=yellow, confirmed=green, cancelled=red, no_response=gray)
- [ ] Clean up temp call audio files after call ends
- [ ] Test full end-to-end flow

---

## Call Flow Summary

```
Customer places order on webpage
        │
        ▼
Backend saves order (status: pending)
        │
        ▼
Background task: stitch audio
  greeting + name + store_intro + amount + instructions
        │
        ▼
Twilio initiates outbound call
        │
        ▼
Customer phone rings → answers
        │
        ▼
Audio plays (personalized message)
        │
        ├── Presses 1 → thankyou.mp3 → call ends → status: confirmed
        ├── Presses 2 → cancelled.mp3 → call ends → status: cancelled
        └── No response → call ends → status: no_response
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
| ElevenLabs Voice ID (Urdu) | Urdu voice for Urdu clients |
| ElevenLabs Voice ID (English) | English voice for English clients |

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
