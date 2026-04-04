# Robocall Order Confirmation System

A SaaS product targeting Pakistani e-commerce businesses that receive Cash on Delivery (COD) orders. The core problem: a large percentage of COD orders are rejected at delivery, causing losses for store owners. This system automatically calls customers after order placement with a personalized AI voice message and captures their confirmation or cancellation via keypress — reducing failed deliveries.

**Business model:** Charge stores per call (~PKR 6/call). Cost per call is ~PKR 2.65 leaving ~55% margin at scale.

---

## Project Components

- **API** (`api/`, port 8001) — core business logic only. No UI. Handles audio generation, Twilio calling, and webhook processing.
- **Demo** (`demo/`, port 8000) — UI only. Login, order placement form, and live dashboard. Communicates with the API via `httpx` background tasks.
- **Scheduler** — retry failed/no-answer calls, call scheduling window (planned)
- **Public API** — `/v1/` REST API for direct third-party integrations (planned)
- **Shopify App** — auto-trigger calls on COD order creation via Shopify webhook (planned)
- **WooCommerce Extension** — WordPress plugin for WooCommerce stores (planned)
- **Store Dashboard** — per-store order view, stats, settings, API key management (planned)
- **Admin Panel** — manage stores, approve/reject onboarding requests, system health (planned)
- **Public Website** — marketing site with store onboarding and admin approval flow (planned)

For full phase-by-phase breakdown see `plan.md`.

---

## Tech Stack

| Layer | Tool |
|---|---|
| Backend | Python + FastAPI |
| Frontend | HTML + Tailwind CSS v4 |
| Database | MySQL + SQLAlchemy |
| TTS / Voice | ElevenLabs API (`eleven_v3` model) |
| Audio Stitching | pydub + ffmpeg |
| Outbound Calling | Twilio (demo) → Local SIP trunk (production) |
| Package Manager | uv (Python), npm (Node/Tailwind) |
| Server | AWS EC2 (Amazon Linux) + Nginx + systemd |

---

## Commands

```bash
# Start all services
uv run main.py

# Start individually
uv run uvicorn api.main:app --port 8001 --reload
uv run uvicorn demo.main:app --port 8000 --reload

# Database management
uv run manage_db.py migrate          # Create/verify all tables
uv run manage_db.py seed             # Insert demo stores
uv run manage_db.py truncate         # Clear orders, customer_names, order_amounts + audio cache
uv run manage_db.py truncate --all   # Also truncates stores
uv run manage_db.py drop             # Drop and recreate customer_names and order_amounts

# Audio generation
uv run generate_static_audio.py           # Generate missing static + store audio only
uv run generate_static_audio.py --fresh   # Clear all audio first, then regenerate

# Tailwind CSS
npm run css:build   # Build minified CSS
npm run css:watch   # Watch mode during development

# Deploy to production
./deploy.sh
```

---

## Implementation

All development phases, completed work, and upcoming features are tracked in [`plan.md`](plan.md).

---

## Architecture

### Audio Pipeline

All audio lives under `audio/`:

```
audio/
├── static/{urdu,english}/        # key_prompt, confirmed, cancelled, no_response — generated once
├── stores/{store_id}_{lang}.mp3  # per-store sentence — generated once per store
├── names/{urdu,english}/         # greeting+name — cached per unique first name + language
├── amounts/{urdu,english}/       # amount audio — cached per unique amount + language
└── calls/{order_id}.mp3          # stitched call audio — generated per order
```

Caching is DB-driven: `customer_names` and `order_amounts` tables track what has been generated. `tts.py` checks these tables before calling ElevenLabs — never re-generates if a record exists.

### Database Tables

- `stores` — store accounts (never truncated in normal operations)
- `orders` — one per placed order, status: pending/confirmed/cancelled/no_response
- `customer_names` — tracks generated greeting audio per first_name + language
- `order_amounts` — tracks generated amount audio per amount + language
- `store_requests` (planned) — store onboarding requests pending admin approval

---

## Important Conventions

- **Never push to GitHub without being asked**
- **Both languages always generated** for every store's audio regardless of their language setting
- **`generate_static_audio.py` does NOT truncate the DB** — use `manage_db.py truncate` separately to avoid wasting ElevenLabs credits
- **Urdu amounts** use a custom word converter — never use Arabic numerals in Urdu TTS text
- **`message.txt` and `twilio_*.txt`** are scratch correspondence files, not part of the app
