from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

from routes import auth, products, search, orders, inventory, agent, analytics, demand, user, reviews

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Smarter BlinkIt API starting up (Memory Optimized)...")
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
