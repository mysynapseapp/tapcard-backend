from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import httpx
import asyncio

from routers import auth, profile, social_links, portfolio, work_experience, qr_code, analytics, social
from database import engine, Base
import models

# Constants
APP_URL = "https://tapcard-backend-gkql.onrender.com"
PING_INTERVAL = 5 * 60  # 5 minutes

# Lifespan context manager for startup and shutdown logic
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ✅ On Startup
    print("🚀 App is starting up...")

    # Create DB tables
    Base.metadata.create_all(bind=engine)

    # Start self-ping loop in background
    async def self_ping():
        await asyncio.sleep(5)  # small delay to let server start fully
        while True:
            try:
                async with httpx.AsyncClient() as client:
                    res = await client.get(APP_URL)
                    print(f"✅ Self-ping: {res.status_code}")
            except Exception as e:
                print(f"❌ Self-ping failed: {e}")
            await asyncio.sleep(PING_INTERVAL)

    asyncio.create_task(self_ping())

    yield  # 👈 App runs here

    # ❌ On Shutdown (if needed)
    print("🛑 App is shutting down...")

# Create FastAPI app
app = FastAPI(title="User Profile API", lifespan=lifespan, redirect_slashes=False)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(profile.router, prefix="/api/user", tags=["profile"])
app.include_router(social_links.router, prefix="/api/user", tags=["social_links"])
app.include_router(portfolio.router, prefix="/api/user/portfolio", tags=["portfolio"])
app.include_router(work_experience.router, prefix="/api/user/work-experience", tags=["work_experience"])
app.include_router(qr_code.router, prefix="/api/user/qr-code", tags=["qr_code"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(social.router, prefix="/api/social", tags=["social"])

# Root route
@app.get("/", tags=["root"])
async def root():
    return {"message": "Welcome to the User Profile API. Visit /docs for API documentation."}
