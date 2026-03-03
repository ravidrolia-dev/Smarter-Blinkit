from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

load_dotenv()

from routes import auth, products, search, orders, inventory, agent, analytics

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Smarter BlinkIt API starting up...")
    yield
    print("🛑 Smarter BlinkIt API shutting down...")

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

@app.get("/")
async def root():
    return {"message": "Smarter BlinkIt API", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "ok"}
