from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, profile, social_links, portfolio, work_experience, qr_code, analytics
from database import engine, SessionLocal, Base

app = FastAPI(title="User Profile API")

@app.get("/", tags=["root"])
async def root():
    return {"message": "Welcome to the User Profile API. Visit /docs for API documentation."}

# CORS middleware (allow all origins for now)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(profile.router, prefix="/api/user", tags=["profile"])
app.include_router(social_links.router, prefix="/api/user/social-links", tags=["social_links"])
app.include_router(portfolio.router, prefix="/api/user/portfolio", tags=["portfolio"])
app.include_router(work_experience.router, prefix="/api/user/work-experience", tags=["work_experience"])
app.include_router(qr_code.router, prefix="/api/user/qr-code", tags=["qr_code"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])

from database import get_db

# Dependency to get DB session
# Removed get_db function here since imported from database.py

# Create tables
def init_db():
    import models
    Base.metadata.create_all(bind=engine)

@app.on_event("startup")
def on_startup():
    init_db()