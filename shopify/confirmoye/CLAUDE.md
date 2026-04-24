# ConfirmOye Shopify App

Shopify app that listens for COD orders via webhook and forwards them to the ConfirmOye Python API, which triggers an automated voice confirmation call to the customer.

---

## Stack

- React Router 7 + Shopify App Bridge
- Prisma (MySQL) — session + settings storage only
- `shopify app dev` for local development (Cloudflare tunnel required for webhooks)

## Commands

```bash
npm run dev                          # Start dev server (shopify app dev)
npx prisma migrate dev --name <name> # Run migrations
npx prisma studio                    # Browse database
```

---

## Python Backend API

**Base URL:** `process.env.API_URL` (e.g. `https://api-robo.aikpie.com/v1`)

### Authentication

All requests to the backend require:
```
X-Api-Key: <store_api_key>
```

The API key is stored per-store in the local `Settings` table. It is issued by the Python backend when a store registers.

---

### Endpoints

#### POST /orders — Place Order
Triggers a new COD confirmation call.

**Request:**
```json
{
  "customer_name": "string",
  "phone": "string",
  "order_amount": 1500.00,
  "order_number": "string | null"
}
```

**Response 201:**
```json
{
  "status": true,
  "data": {
    "order_id": 1,
    "order_number": "1001",
    "status": "pending"
  }
}
```

**Response 409** (duplicate order_number):
```json
{
  "status": false,
  "reason": "Order number '1001' already exists."
}
```

---

#### GET /orders — List Orders (paginated)

**Query params:**
```
page:      integer (default=1)
page_size: integer (default=20, max=100)
```

**Response 200:**
```json
{
  "status": true,
  "data": {
    "page": 1,
    "page_size": 20,
    "total": 150,
    "orders": [
      {
        "order_id": 1,
        "order_number": "1001",
        "customer_name": "Ahmed",
        "phone": "03001234567",
        "order_amount": 1500.00,
        "status": "confirmed",
        "call_attempts": 1,
        "created_at": "2026-04-21T10:00:00Z"
      }
    ]
  }
}
```

**Note:** `status` values: `pending` | `confirmed` | `cancelled` | `no_response`

---

#### GET /orders/{identifier} — Get Single Order

`identifier` is either an integer order ID or a string order_number.

**Response 200:**
```json
{
  "status": true,
  "data": {
    "order_id": 1,
    "order_number": "1001",
    "customer_name": "Ahmed",
    "phone": "03001234567",
    "order_amount": 1500.00,
    "status": "confirmed",
    "call_attempts": 1,
    "created_at": "2026-04-21T10:00:00Z",
    "updated_at": "2026-04-21T10:05:00Z"
  }
}
```

**Response 404:**
```json
{
  "status": false,
  "reason": "Order not found."
}
```

---

### Error Response Format

All errors follow this shape:
```json
{
  "status": false,
  "reason": "Human-readable message"
}
```

| Code | Meaning |
|------|---------|
| 401 | Invalid or missing X-Api-Key |
| 404 | Order not found |
| 409 | Duplicate order_number |
| 429 | Rate limit exceeded (60 req/min per key) |

---

## Webhook Handler

`app/routes/webhooks.orders.create.jsx` receives `orders/create` from Shopify.

**What to extract from Shopify payload:**
```js
{
  shop,                                          // from authenticate.webhook()
  shopify_order_id:  order.id,
  order_number:      String(order.order_number),
  customer_name:     order.customer?.first_name
                     || order.billing_address?.first_name,
  phone:             order.phone
                     || order.billing_address?.phone
                     || order.customer?.phone,
  order_amount:      parseFloat(order.total_price),
}
```

**What to POST to backend:**
```json
{
  "customer_name": "Ahmed",
  "phone": "03001234567",
  "order_amount": 1500.00,
  "order_number": "1001"
}
```

**COD detection** — check `order.payment_gateway`:
- `"cash_on_delivery"`
- `"cod"`
- any value containing `"cod"` (case-insensitive)

---

## Local Database (Prisma)

Only two tables — all business data lives in the Python backend.

### Session
Managed automatically by `@shopify/shopify-app-react-router`. Do not touch.

### Settings
```prisma
model Settings {
  id        Int      @id @default(autoincrement())
  shop      String   @unique        // e.g. "mystore.myshopify.com"
  apiKey    String                  // issued by Python backend
  enabled   Boolean  @default(true) // merchant can pause calls
  createdAt DateTime @default(now())
}
```

---

## Routes

| File | URL | Purpose |
|------|-----|---------|
| `app._index.jsx` | `/app` | Orders page (fetches from Python API) |
| `app.settings.jsx` | `/app/settings` | API key + enable/disable toggle |
| `webhooks.orders.create.jsx` | `/webhooks/orders/create` | Receives Shopify order webhooks |
| `webhooks.app.uninstalled.jsx` | `/webhooks/app/uninstalled` | Cleanup on uninstall |

---

## Environment Variables

```env
DATABASE_URL=mysql://root@localhost:3306/robocall_shopify
API_URL=https://api-robo.aikpie.com/v1
SHOPIFY_API_KEY=...       # auto-managed by shopify app dev
SHOPIFY_API_SECRET=...    # auto-managed by shopify app dev
```
