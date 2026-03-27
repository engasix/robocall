# Robocall — AI Order Confirmation System

An automated voice call system for COD (Cash on Delivery) e-commerce orders. When a customer places an order, the system calls them with a personalized AI-generated voice message and captures their confirmation via keypress.

## How It Works

1. Customer places a COD order on the webpage
2. Backend saves the order and triggers a background task
3. Personalized audio is stitched together (greeting + name + store + amount + instructions)
4. Twilio places an outbound call to the customer
5. Customer presses **1** to confirm or **2** to cancel
6. Order status updates live on the dashboard

## Tech Stack

| Layer | Tool |
|---|---|
| Backend | Python + FastAPI |
| Frontend | HTML + Tailwind CSS |
| Outbound Calling | Twilio |
| Text-to-Speech | ElevenLabs |
| Audio Stitching | pydub |
| Database | MySQL + SQLAlchemy |
| Package Manager | uv |

## Features

- Bilingual support — Urdu and English (per store preference)
- Smart name parsing — extracts first name using `nameparser` + Pakistani honorifics (Syed, Muhammad, Abdul, etc.)
- Audio caching — ElevenLabs is called only once per unique name or amount, reused for all future orders
- Live dashboard — auto-refreshing order status with color coding
- Async call triggering — order placement never blocks waiting for the call

## Project Structure

```
robocall/
├── main.py               # FastAPI app entry point
├── config.py             # Environment variables
├── database.py           # Models & DB connection
├── pyproject.toml        # Dependencies (managed by uv)
├── .env                  # API keys (not committed)
│
├── routers/
│   ├── orders.py         # POST /place-order
│   ├── calls.py          # Twilio webhook endpoints
│   └── dashboard.py      # GET /dashboard
│
├── services/
│   ├── tts_service.py    # ElevenLabs TTS + caching
│   ├── audio_service.py  # Audio stitching with pydub
│   └── call_service.py   # Twilio outbound call trigger
│
├── audio/                # Generated audio files (not committed)
│   ├── static/           # Pre-generated static phrases
│   ├── amounts/          # Cached amount audio by DB id
│   ├── stores/           # Store name audio by store id
│   ├── names/            # Customer name audio by DB id
│   └── calls/            # Final stitched call audio (temp)
│
└── templates/
    ├── index.html        # Order placement form
    └── dashboard.html    # Live order status dashboard
```

## Setup

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) — Python package manager
- MySQL database
- Twilio account
- ElevenLabs account

### Installation

```bash
git clone https://github.com/your-username/robocall.git
cd robocall
uv sync
```

### Configuration

Copy `.env` and fill in your credentials:

```bash
cp .env .env.local
```

```env
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=+1xxxxxxxxxx

ELEVENLABS_API_KEY=your_elevenlabs_api_key
ELEVENLABS_VOICE_ID_URDU=your_urdu_voice_id
ELEVENLABS_VOICE_ID_ENGLISH=your_english_voice_id

DATABASE_URL=mysql+pymysql://user:password@localhost:3306/robocall

BASE_URL=http://localhost:8000
```

### Run

```bash
uv run uvicorn main:app --reload
```

App will be available at `http://localhost:8000`.
The database tables are created automatically on startup.

## API Keys Required

| Service | Purpose |
|---|---|
| Twilio Account SID + Auth Token | Outbound calling |
| Twilio Phone Number | Caller ID |
| ElevenLabs API Key | TTS generation |
| ElevenLabs Voice ID (Urdu) | Urdu voice for Urdu-language stores |
| ElevenLabs Voice ID (English) | English voice for English-language stores |

## Production

| Demo | Production |
|---|---|
| Twilio calling | Local Pakistani SIP trunk |
| Local audio files | AWS S3 |
| Single server | Dockerized + Nginx + Gunicorn |
