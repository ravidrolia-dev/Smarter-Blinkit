# Smarter BlinkIt 🛒⚡

> An AI-powered smart marketplace that connects buyers with local sellers — with intent-based search, a recipe agent, face ID login, barcode inventory management, and a live storeboard.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14 (App Router) + TypeScript + Tailwind CSS |
| Backend | FastAPI (Python) + Uvicorn |
| AI/ML | **Gemini (V4 Architecture)**: Optimized sequential fallback (`3.1-flash-lite`, `2.5-flash-lite`, `2.5-flash`) with multi-key rotation and proactive quota management. |
| Search | sentence-transformers (semantic intent-based search) |
| Image System | High-accuracy validation: Unsplash ↔ OpenFoodFacts ↔ OpenBeautyFacts |
| Primary DB | MongoDB (+ Motor for async) |
| Graph DB | Neo4j (SIMILAR_TO, BOUGHT_WITH relationships) |
| Payments | Razorpay (test mode) |
| Barcode | OpenCV + zxing-cpp + pyzbar (Dual-Engine backend pipeline) |
| Face ID | face_recognition (dlib) |
| Market Basket | Apriori Algorithm (mlxtend + pandas) |

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
| `GEMINI_API_KEYS` | (New) Comma-separated list of Gemini API keys for automatic rotation and high-load fallback. |
| `GEMINI_API_KEY` | Legacy single Gemini API key (still supported). |

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
- **High-Accuracy Image System**: Intelligent keyword-to-image mapping verified against Unsplash, OpenFoodFacts, and OpenBeautyFacts. No generic placeholders.
- **Location**: Nearest shops auto-prioritized via GPS + geo-distance
- **Pro Barcode Scanner**: High-accuracy dual-engine backend (OpenCV/ZXing) scanning with OpenFoodFacts auto-fill integration.
- **Razorpay**: Test-mode payment checkout with signature verification
- **Search Hardening**: Optimized JSON array parsing and regex sanitization for error-free natural language queries.

### Stage 2 — Automator
- **Recipe Agent (V4)**: High-efficiency sequential AI architecture. Type "Make Pizza" → AI parses ingredients in batches and finds them in local inventory, even under heavy quota pressure.
- **Neo4j Graph**: Products connected via `BOUGHT_WITH` + `SIMILAR_TO` for smart recommendations

### Stage 3 — Orchestrator
- **Smart Cart Split**: Multi-shop orders grouped by shop with subtotals
- **Live Storeboard**: Auto-refreshing dashboard with charts, leaderboard, order feed
- **Money Map Analytics**: High-fidelity Leaflet + OpenStreetMap geo-heatmap showing real-time sales demand and neighborhood spending density.

### God Mode — Smart Analytics
- **Smart Product Pairing**: AI-powered "Frequently Bought Together" recommendations using Market Basket Analysis (Apriori).
- **Market Insights Portal**: Deep-dive seller dashboard to visualize platform-wide product associations and trigger manual AI model retraining.
- **Upsell Engine**: Multi-stage recommendation placement on Product pages, Cart summaries, and Checkout sidebars.

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
│       │   │   ├── search/        # Smart Search
│       │   │   ├── agent/         # Recipe Agent
│       │   │   ├── cart/          # Cart + Recommendations
│       │   │   └── product/       # Product Detail View
│       │   └── seller/            # Seller portal
│       │       ├── page.tsx       # Dashboard
│       │       ├── insights/      # Market Insights Dashboard
│       │       ├── money-map/     # Geo-demand Analytics
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
│       ├── ai/
│       │   ├── gemini_service.py      # Resilient sequential AI fallback logic
│       │   └── rate_limit_manager.py  # Thread-safe RPM/RPD tracking
│       ├── product_pairing_service.py # Apriori Market Basket Analysis
│       ├── face_auth.py         # face_recognition lib
│       ├── semantic_search.py   # sentence-transformers
│       ├── neo4j_service.py     # Graph DB operations
│       ├── recipe_agent.py      # Upgraded Recipe Agent logic
│       ├── jwt_utils.py
│       └── dependencies.py
└── .env.example
```
