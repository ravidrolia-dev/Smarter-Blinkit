from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

from routes import auth, products, search, orders, inventory, agent, analytics, demand, user, reviews

def _preload_model():
    """Load the sentence-transformers model (called in background daemon thread)."""
    try:
        from services.semantic_search import get_model
        get_model()
    except Exception as e:
        print(f"Semantic model preload failed: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Smarter BlinkIt API starting up...")
    # Kick off model loading in a daemon background thread — does NOT block server startup.
    # First search request will use the cached model once it finishes loading (~30s).
    import threading
    t = threading.Thread(target=_preload_model, daemon=True, name="model-preload")
    t.start()
    yield
    print("Smarter BlinkIt API shutting down...")

app = FastAPI(
    title="Smarter BlinkIt API",
    description="Smart Marketplace with AI Shopping Assistant",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
cors_origins_raw = os.getenv("CORS_ORIGINS", "http://localhost:3000")
# Clean and validate origins: strip whitespace, remove trailing slashes, skip empty
allow_origins = [o.strip().rstrip("/") for o in cors_origins_raw.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Request Logging Middleware (for debugging CORS/OPTIONS issues on Render)
@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Log incoming request basic info
    origin = request.headers.get("origin")
    method = request.method
    path = request.url.path
    print(f"DEBUG: Incoming {method} request to {path} | Origin: {origin}")
    
    response = await call_next(request)
    
    print(f"DEBUG: Response for {method} {path} | Status: {response.status_code}")
    return response

# Routers
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(products.router, prefix="/products", tags=["Products"])
app.include_router(search.router, prefix="/search", tags=["Search"])
app.include_router(orders.router, prefix="/orders", tags=["Orders"])
app.include_router(inventory.router, prefix="/inventory", tags=["Inventory"])
app.include_router(agent.router, prefix="/agent", tags=["Recipe Agent"])
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
app.include_router(demand.router, prefix="/demand", tags=["Demand"])
app.include_router(user.router, prefix="/user", tags=["User"])
app.include_router(reviews.router, prefix="/reviews", tags=["Reviews"])

@app.get("/")
async def root():
    return {"message": "Smarter BlinkIt API", "status": "running"}

@app.get("/health")
async def health():
    # Trigger hot reload to reset MongoDB connections
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
