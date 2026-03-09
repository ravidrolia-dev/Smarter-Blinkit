from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

from routes import auth, products, search, orders, inventory, agent, analytics, demand

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

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(products.router, prefix="/products", tags=["Products"])
app.include_router(search.router, prefix="/search", tags=["Search"])
app.include_router(orders.router, prefix="/orders", tags=["Orders"])
app.include_router(inventory.router, prefix="/inventory", tags=["Inventory"])
app.include_router(agent.router, prefix="/agent", tags=["Recipe Agent"])
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
app.include_router(demand.router, prefix="/demand", tags=["Demand"])

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
