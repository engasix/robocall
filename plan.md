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
├── main.py                   # Entry point — starts API + Demo (and future services)
├── config.py                 # Shared environment variables & settings
├── database.py               # Shared MySQL models & connection
├── generate_static_audio.py  # Reset script: clears all audio, truncates DB, regenerates static
├── .env                      # API keys (never committed)
├── plan.md
│
├── api/                      # Core API — all business logic
│   ├── main.py               # FastAPI app (port 8001)
│   ├── routers/
│   │   └── orders.py         # POST /orders/process
│   └── services/
│       ├── tts.py            # ElevenLabs TTS generation & caching
│       ├── audio_stitcher.py # Audio stitching with pydub
│       └── name_utils.py     # Pakistani name extraction logic
│
├── demo/                     # Demo app — UI only, delegates to API
│   ├── main.py               # FastAPI app (port 8000)
│   ├── routers/
│   │   ├── auth.py           # GET/POST /login, GET /logout
│   │   └── orders.py         # POST /place-order → calls API
│   ├── templates/
│   │   ├── login.html
│   │   ├── index.html
│   │   └── dashboard.html
│   └── static/css/
│       ├── input.css         # Tailwind v4 source
│       └── style.css         # Compiled output
│
└── audio/                    # Shared generated audio (gitignored)
    ├── static/
    │   ├── urdu/             # key_prompt, confirmed, cancelled, no_response
    │   └── english/
    ├── stores/               # Per-store sentences — both languages for every store
    ├── names/
    │   ├── urdu/             # Cached greeting+name per customer first name
    │   └── english/
    ├── amounts/
    │   ├── urdu/             # Cached amount audio
    │   └── english/
    └── calls/                # Final stitched call audio per order
```

---

## Implementation Phases

### Phase 1 — Project Setup ✅
- [x] Initialize FastAPI project with `uv` package manager
- [x] Setup `.env` with Twilio & ElevenLabs credentials
- [x] Setup MySQL database with `stores`, `orders`, `customer_names`, `order_amounts` tables
- [x] Install all dependencies (`fastapi`, `uvicorn`, `twilio`, `pydub`, `elevenlabs`, `sqlalchemy`, `pymysql`, `python-dotenv`, `num2words`, `bcrypt`, etc.)
- [x] Restructured into `api/` and `demo/` separation with shared root-level config and database
- [x] Root `main.py` starts all services together

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
- [x] Zero inline styles — all styling in `input.css` component classes

---

### Phase 3 — TTS Audio Setup ✅
- [x] `api/services/tts.py` — ElevenLabs integration (`eleven_v3` model)
- [x] Shared static segments generated in both languages:
  - `audio/static/urdu/` — key_prompt, confirmed, cancelled, no_response (proper Urdu script)
  - `audio/static/english/` — same in English
- [x] Per-store sentence audio — **both languages generated for every store** regardless of current language setting:
  - Urdu: `"{store_name} پر آرڈر دینے کا شکریہ، آپ کے آرڈر کی رقم ہے"`
  - English: `"Thanks for placing order on {store_name}, your order amount is"`
- [x] Greeting + name as single TTS call (cached per first name per language):
  - Urdu: `"السلام علیکم {first_name}"`
  - English: `"Hello {first_name}"`
- [x] Amount audio with currency — custom Urdu number-to-words converter (e.g. `"تین ہزار روپے"`), `num2words` for English (e.g. `"three thousand rupees"`)
- [x] DB-driven caching — `customer_names` and `order_amounts` tables track generated audio per language
- [x] Configurable voice settings per language in `config.py` — speed, stability, similarity_boost, style, speaker_boost
- [x] `generate_static_audio.py` — regenerates static and store audio (skips existing; `--fresh` flag clears all first)
- [x] `manage_db.py` — separate DB management script: `migrate`, `truncate` (clears DB + audio cache), `drop`

---

### Phase 4 — Audio Stitching Service ✅
- [x] `api/services/audio_stitcher.py` using `pydub`
- [x] `build_call_audio(order_id, customer_name, store_id, store_name, order_amount, language)`:
  1. Generate/retrieve greeting+name audio (cached per first name)
  2. Load pre-generated store sentence
  3. Generate/retrieve amount audio (cached per amount)
  4. Load shared key_prompt static segment
  5. Concatenate with natural pauses → export as `audio/calls/{order_id}.mp3`
- [x] Triggered as FastAPI `BackgroundTask` — order response returns instantly

**Call Script Flow:**
```
[greeting + name]  →  [store sentence]  →  [amount]  →  [key prompt]

Urdu:    "السلام علیکم Asif" | "Urdu Scents پر آرڈر دینے کا شکریہ..." | "ڈیڑھ ہزار" | "1 دبائیں یا 2..."
English: "Hello Asif" | "Thanks for placing order on English Scents..." | "one thousand, five hundred" | "Press 1 or 2..."
```

---

### Phase 5 — Server Deployment ✅
- [x] Provision AWS EC2 instance (Amazon Linux)
- [x] Install dependencies: Python 3.11, uv, MariaDB, ffmpeg (static build), Nginx, Node.js via NVM
- [x] Configure Nginx as reverse proxy:
  - `robo.aikpie.com` → Demo app (port 8000) via `demo.conf`
  - `api-robo.aikpie.com` → API (port 8001) via `api.conf`
- [x] Setup systemd services (`robocall-api`, `robocall-demo`) to keep services running
- [x] Configure firewall via AWS Security Groups (ports 22, 80, 443)
- [x] Point domain DNS to server IP
- [x] Setup SSL via Let's Encrypt (`robo.aikpie.com`, `api-robo.aikpie.com`)
- [x] Set production `.env` with live credentials and `BASE_URL`, `API_URL`
- [x] Run `manage_db.py migrate` + `seed` + `generate_static_audio.py` on server
- [x] `deploy.sh` — one-command deployer: SSHes into server, pulls latest code, restarts services

---

### Phase 6 — Calling Service (Twilio Integration) ✅
- [x] `api/services/call_service.py` — `trigger_call(order_id, phone)`
  - Serves stitched MP3 via public URL (`API_URL/audio/calls/{order_id}.mp3`)
  - Initiates Twilio outbound call with TwiML — `<Play>` inside `<Gather>` so keypress is collected while audio plays
  - `<Redirect>` fallback ensures no-input triggers the webhook as `no_response`
- [x] Wired into `api/routers/orders.py` after `build_call_audio()`

---

### Phase 7 — Twilio Webhooks ✅
- [x] `api/routers/webhooks.py` registered at `/webhook`
- [x] `POST /webhook/keypress/{order_id}`:
  - Digit `1` → status: `confirmed` → plays `confirmed.mp3` in store's language
  - Digit `2` → status: `cancelled` → plays `cancelled.mp3` in store's language
  - No input / other → status: `no_response` → plays `no_response.mp3`
- [x] `POST /webhook/call-status/{order_id}` — marks order as `no_response` on busy/failed/no-answer/canceled

---

### Phase 8 — Order Placement Endpoint ✅
- [x] Demo `POST /place-order` — saves order to DB, returns instantly
- [x] Demo background task calls `POST /orders/process` on the API via httpx
- [x] API `POST /orders/process` — runs `build_call_audio()`, then triggers call (Phase 6)
- [x] `GET /api/orders` — returns all orders for dashboard (store filter ready for future)

---

### Phase 9 — Dashboard & Polish ✅
- [x] Live order status dashboard with 5s polling
- [x] Status badges: pending=amber, confirmed=green, cancelled=red, no_response=gray
- [x] End-to-end testing — full call flow verified on production server
- [ ] Clean up call audio files after call ends (future cleanup task)

---

## Call Flow Summary

```
Customer places order on webpage
        │
        ▼
Demo saves order to DB (status: pending) → responds instantly
        │
        ▼
Demo background task → POST /orders/process to API
        │
        ▼
API: build_call_audio() → greeting+name | store sentence | amount | key prompt
        │
        ▼
API: trigger_call() → Twilio outbound call (Phase 6)
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

## Running the Project

```bash
# Start all services
uv run main.py

# Or individually:
uv run uvicorn api.main:app --port 8001 --reload   # API
uv run uvicorn demo.main:app --port 8000 --reload  # Demo

# Regenerate all audio (resets DB tables except stores)
uv run generate_static_audio.py
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

---

### Phase 10 — API Security Layer (Build First)
- [ ] Generate API keys per store — stored in `stores` table (hashed)
- [ ] `X-API-Key` header authentication middleware for all `/orders/*` and `/webhook/*` routes
- [ ] Rate limiting per API key — max requests per minute to prevent abuse
- [ ] IP whitelisting option per store (optional, for enterprise stores)
- [ ] API key management endpoints:
  - `POST /auth/generate-key` — generate a new API key for a store
  - `POST /auth/revoke-key` — revoke an existing key
- [ ] Secure Twilio webhooks — validate `X-Twilio-Signature` on all incoming webhook requests
- [ ] Add API key to demo→API communication in `demo/routers/orders.py`

---

### Phase 11 — Scheduler Service
- [ ] `scheduler/main.py` — standalone service (runs as separate process)
- [ ] Retry logic — if call status is `no_response`, retry after configurable delay (e.g. 10 mins)
- [ ] Max retry attempts per order (e.g. 3 attempts)
- [ ] Call scheduling window — only call between configured hours (e.g. 9AM–9PM)
- [ ] Track retry attempts in `orders` table (`retry_count` column)
- [ ] Wire into `main.py` as a subprocess alongside API and Demo

---

### Phase 12 — Store Dashboard
- [ ] Each store logs in and sees only their own orders
- [ ] Order stats: total orders, confirmed %, cancelled %, no response %
- [ ] Call history with timestamps and duration
- [ ] Store settings page — update language, voice settings, business name
- [ ] API key management UI — generate/revoke keys from dashboard
- [ ] Usage tracking — calls made this month, credits remaining

---

### Phase 13 — Admin Panel
- [ ] Super admin login (separate from store login)
- [ ] Manage all stores — view, activate, deactivate
- [ ] Global call volume and stats across all stores
- [ ] Billing overview — usage per store, revenue tracking
- [ ] System health — API status, Twilio balance, ElevenLabs credits

---

### Phase 14 — Public API
- [ ] Public-facing REST API for direct integration
- [ ] Authentication via API key (`X-API-Key` header — built in Phase 10)
- [ ] Endpoints:
  - `POST /v1/orders` — place an order and trigger a confirmation call
  - `GET /v1/orders/{order_id}` — get order status
  - `GET /v1/orders` — list all orders (paginated)
- [ ] API documentation (Swagger/OpenAPI — auto-generated by FastAPI)
- [ ] Webhooks for order status updates — stores can register a callback URL to receive status updates in real time
- [ ] SDK (future) — Python and JavaScript client libraries

---

### Phase 15 — Shopify App
- [ ] Shopify app setup — public app listed on Shopify App Store
- [ ] OAuth flow — store owner installs app and grants permissions
- [ ] Shopify webhook — listen to `orders/create` event
- [ ] On new COD order → automatically call `POST /v1/orders` on our Public API
- [ ] App settings page inside Shopify admin — configure language, API key, calling hours
- [ ] Order metafield update — write confirmation status back to Shopify order

---

### Phase 16 — WooCommerce Extension
- [ ] WordPress plugin — install on any WooCommerce store
- [ ] Hook into `woocommerce_checkout_order_processed` action
- [ ] On new COD order → call `POST /v1/orders` on our Public API
- [ ] Plugin settings page — API key, language, calling hours
- [ ] Order note update — write confirmation status back to WooCommerce order notes

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
