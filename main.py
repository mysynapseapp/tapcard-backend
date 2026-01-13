from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio

from routers import (
    auth,
    profile,
    social_links,
    portfolio,
    work_experience,
    qr_code,
    analytics,
    social,
)
from database import engine, Base
import models

# Constants
APP_URL = "https://tapcard-backend.onrender.com"
PING_INTERVAL = 5 * 60  # 5 minutes


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ✅ On Startup
    print("🚀 App is starting up...")

    # Create DB tables
    Base.metadata.create_all(bind=engine)

    # Start self-ping loop in background
    async def self_ping():
        await asyncio.sleep(5)
        while True:
            try:
                import urllib.request
                with urllib.request.urlopen(APP_URL) as response:
                    print(f"✅ Self-ping: {response.status}")
            except Exception as e:
                print(f"❌ Self-ping failed: {e}")
            await asyncio.sleep(PING_INTERVAL)

    asyncio.create_task(self_ping())
    yield
    print("🛑 App is shutting down...")


# ✅ IMPORTANT: DO NOT disable redirect_slashes
app = FastAPI(
    title="User Profile API",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- ROUTERS ---------------- #

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(profile.router, prefix="/api/user", tags=["profile"])

# These routers already define their own prefixes
app.include_router(social_links.router)
app.include_router(portfolio.router)
app.include_router(work_experience.router)
app.include_router(qr_code.router)


app.include_router(analytics.router)
app.include_router(social.router)

# Root route
@app.get("/", tags=["root"])
async def root():
    return {
        "message": "Welcome to the User Profile API. Visit /docs for API documentation."
    }
