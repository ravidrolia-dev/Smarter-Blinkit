# Smarter BlinkIt 🛒⚡

> An AI-powered smart marketplace that connects buyers with local sellers — with intent-based search, a recipe agent, face ID login, barcode inventory management, and a live storeboard.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14 (App Router) + TypeScript + Tailwind CSS |
| Backend | FastAPI (Python) + Uvicorn |
| AI/ML | Google Gemini (recipe agent), sentence-transformers (semantic search), face_recognition (dlib) |
| Primary DB | MongoDB (+ Motor for async) |
| Graph DB | Neo4j (SIMILAR_TO, BOUGHT_WITH relationships) |
| Payments | Razorpay (test mode) |
| Barcode | QuaggaJS (browser camera) |

---

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- MongoDB running locally (`mongod`)
- **Optional:** Neo4j (for graph recommendations)

### 1. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Copy env file and fill in your keys
copy .env.example .env      # Windows
# cp .env.example .env      # Mac/Linux

# Seed demo data (optional but recommended)
python seed.py

# Start the API server
uvicorn main:app --reload --port 8000
```

API docs available at: **http://localhost:8000/docs**

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start Next.js dev server
npm run dev
```

App available at: **http://localhost:3000**

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Description |
|----------|-------------|
| `MONGO_URI` | MongoDB connection string |
| `JWT_SECRET` | Secret key for JWT signing |
| `NEO4J_URI` | Neo4j bolt connection (optional) |
| `RAZORPAY_KEY_ID` | Razorpay test key ID |
| `RAZORPAY_KEY_SECRET` | Razorpay test secret |
| `GEMINI_API_KEY` | Google Gemini API key |

Get Gemini API key: [aistudio.google.com](https://aistudio.google.com)  
Get Razorpay test keys: [dashboard.razorpay.com](https://dashboard.razorpay.com)

### Frontend (`frontend/.env.local`)

```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_RAZORPAY_KEY_ID=rzp_test_...
```

---

## Demo Credentials (after running `seed.py`)

| Role | Email | Password |
|------|-------|----------|
| Buyer | buyer@demo.com | demo1234 |
| Seller 1 | seller@demo.com | demo1234 |
| Seller 2 | seller2@demo.com | demo1234 |

---

## Feature Overview

### Stage 1 — Foundation
- **Dual Login**: Buyer / Seller roles with separate dashboards
- **Face ID**: Register face during signup, login by looking at camera
- **Intent Search**: "I have a cold" → surfaces Honey, Ginger Tea, Tulsi Drops
- **Location**: Nearest shops auto-prioritized via GPS + geo-distance
- **Barcode Scanner**: Sellers scan boxes to update inventory
- **Razorpay**: Test-mode payment checkout with signature verification

### Stage 2 — Automator
- **Recipe Agent**: Type "Make Pizza for 4" → AI finds all ingredients from local inventory
- **Neo4j Graph**: Products connected via `BOUGHT_WITH` + `SIMILAR_TO` for smart recommendations

### Stage 3 — Orchestrator
- **Smart Cart Split**: Multi-shop orders grouped by shop with subtotals
- **Live Storeboard**: Auto-refreshing dashboard with charts, leaderboard, order feed

### Bonus — God Mode
- **Money Map**: API endpoint returning geo-heatmap data for neighborhood analytics

---

## Project Structure

```
Smarter-Blinkit/
├── frontend/        # Next.js 14 app (yellow + white theme)
│   └── src/
│       ├── app/
│       │   ├── page.tsx           # Landing page
│       │   ├── login/             # Login (password + face ID)
│       │   ├── register/          # 2-step registration
│       │   ├── buyer/             # Buyer portal
│       │   │   ├── page.tsx       # Dashboard
│       │   │   ├── search/        # Smart search
│       │   │   ├── agent/         # Recipe Agent
│       │   │   ├── cart/          # Cart + Razorpay
│       │   │   └── orders/        # Order history
│       │   └── seller/            # Seller portal
│       │       ├── page.tsx       # Dashboard
│       │       ├── inventory/     # Product table
│       │       ├── barcode/       # Barcode scanner
│       │       ├── orders/        # Live Storeboard
│       │       └── products/new/  # Add product
│       ├── components/
│       │   └── DashboardLayout.tsx
│       └── lib/
│           ├── api.ts             # Axios API client
│           └── auth-context.tsx   # JWT auth context
├── backend/         # FastAPI Python server
│   ├── main.py
│   ├── database.py
│   ├── seed.py
│   ├── requirements.txt
│   ├── routes/
│   │   ├── auth.py       # Login, register, face-login
│   │   ├── products.py   # CRUD + embeddings + recommendations
│   │   ├── search.py     # Semantic intent search
│   │   ├── orders.py     # Cart, Razorpay, smart split
│   │   ├── inventory.py  # Barcode lookup + stock
│   │   ├── agent.py      # Recipe agent endpoint
│   │   └── analytics.py  # Storeboard + money map
│   └── services/
│       ├── face_auth.py         # face_recognition lib
│       ├── semantic_search.py   # sentence-transformers
│       ├── neo4j_service.py     # Graph DB operations
│       ├── recipe_agent.py      # Gemini integration
│       ├── jwt_utils.py
│       └── dependencies.py
└── .env.example
```
