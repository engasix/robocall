# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Start all services (API + Demo)
uv run main.py

# Start individually
uv run uvicorn api.main:app --port 8001 --reload
uv run uvicorn demo.main:app --port 8000 --reload

# Database management
uv run manage_db.py migrate          # Create/verify all tables
uv run manage_db.py seed             # Insert demo stores
uv run manage_db.py truncate         # Clear orders, customer_names, order_amounts + audio cache
uv run manage_db.py truncate --all   # Also truncates stores
uv run manage_db.py drop             # Drop and recreate customer_names and order_amounts (schema change)

# Audio generation
uv run generate_static_audio.py           # Generate missing static + store audio only
uv run generate_static_audio.py --fresh   # Clear all audio first, then regenerate

# Tailwind CSS
npm run css:build   # Build minified CSS
npm run css:watch   # Watch mode during development

# Deploy to production
./deploy.sh
```

## Architecture

Two FastAPI services share a single MySQL database:

- **`api/`** (port 8001) — core business logic only. No UI. Handles audio generation, Twilio calling, and webhook processing.
- **`demo/`** (port 8000) — UI only. Handles login, order placement form, and dashboard. Communicates with the API via `httpx` background tasks.
- **`config.py`** and **`database.py`** are at the root and shared by both services.

### Request Flow
1. Customer places order on `demo/` → saved to DB instantly → background task fires
2. Background task POSTs to `api/orders/process`
3. API stitches call audio, then triggers Twilio outbound call
4. Twilio plays audio → customer presses 1/2 → webhook hits `api/webhook/keypress/{order_id}`
5. Order status updated in DB → demo dashboard polls and reflects live status

### Audio Pipeline
All audio lives under `audio/` with this structure:
```
audio/
├── static/{urdu,english}/     # key_prompt, confirmed, cancelled, no_response — generated once
├── stores/{store_id}_{lang}.mp3  # per-store sentence — generated once per store
├── names/{urdu,english}/      # greeting+name — cached per unique first name per language
├── amounts/{urdu,english}/    # amount audio — cached per unique amount per language
└── calls/{order_id}.mp3       # stitched call audio — generated per order
```

**Caching is DB-driven**: `customer_names` and `order_amounts` tables track what has been generated. `tts.py` checks these tables before calling ElevenLabs — never re-generates if a record exists.

### Key Files
- `api/services/tts.py` — ElevenLabs TTS (`eleven_v3` model). Voice settings and voice IDs configured in `config.py` under `VOICE_SETTINGS_URDU/ENGLISH`.
- `api/services/audio_stitcher.py` — stitches segments with pydub: greeting → store sentence → amount → key_prompt
- `api/services/call_service.py` — Twilio outbound call with `<Play>` inside `<Gather>` for keypress capture
- `api/routers/webhooks.py` — handles Twilio keypress and call-status callbacks; plays response audio in the store's language
- `api/services/name_utils.py` — extracts first name from full Pakistani names, handles honorifics
- `demo/routers/auth.py` — bcrypt login/logout with session management

### CSS
Tailwind CSS v4 with a custom warm charcoal theme (`#33302B`). Source: `demo/static/css/input.css` → compiled to `demo/static/css/style.css`. All styling uses component classes defined in `input.css` — zero inline styles in HTML templates.

### Database Tables
- `stores` — store accounts (never truncated in normal operations)
- `orders` — one per placed order, status: pending/confirmed/cancelled/no_response
- `customer_names` — tracks generated greeting audio per first_name + language
- `order_amounts` — tracks generated amount audio per amount + language
- `store_requests` (planned Phase 17) — store onboarding requests pending admin approval

## Project Vision

A SaaS product targeting Pakistani e-commerce businesses that receive Cash on Delivery (COD) orders. The core problem: a large percentage of COD orders are rejected at delivery, causing losses for store owners. This system automatically calls customers after order placement to confirm or cancel — reducing failed deliveries.

**Business model:** Charge stores per call (~PKR 6/call). Cost per call is ~PKR 2.65 leaving ~55% margin at scale.

**Target integrations:** Shopify App Store, WooCommerce plugin, and a Public API for custom integrations.

---

## Planned Components (see plan.md for full detail)

| Phase | Component | Status |
|---|---|---|
| 1–9 | Core system — TTS, audio stitching, Twilio calling, webhooks, dashboard | ✅ Complete |
| 10 | API Security Layer — API key auth, rate limiting, Twilio signature validation | Pending |
| 11 | Scheduler — retry failed calls, call scheduling window | Pending |
| 12 | Public API — `/v1/orders` REST API with API key auth and status webhooks | Pending |
| 13 | Shopify App — auto-trigger calls on COD order creation | Pending |
| 14 | WooCommerce Extension — WordPress plugin for WooCommerce stores | Pending |
| 15 | Store Dashboard — per-store order view, stats, settings, API key management | Pending |
| 16 | Admin Panel — manage stores, approve/reject onboarding requests, system health | Pending |
| 17 | Public Website — marketing site with store onboarding/signup flow | Pending |

**Store onboarding flow (Phase 17):** Store submits registration form → saved to `store_requests` table as `pending` → admin reviews in Admin Panel → on approval, store is created and credentials emailed → on rejection, rejection email sent. Store is never created until admin approves.

---

## Important Conventions

- **Never push to GitHub without being asked** — always wait for explicit instruction
- **Urdu amounts** use a custom word converter in `tts.py` (`_urdu_number()`) — `num2words` does not support Urdu
- **Both languages always generated** for every store's audio regardless of their `language` setting
- **`generate_static_audio.py` does NOT truncate the DB** — use `manage_db.py truncate` for that separately, to avoid wasting ElevenLabs credits
- **`message.txt` and `twilio_*.txt`** are scratch files for correspondence, not part of the app
