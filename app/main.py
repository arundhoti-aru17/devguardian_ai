from fastapi import FastAPI
from app.core.config import settings

from app.api.router import api_router

app = FastAPI(
    title="DevGuardian AI",
    version="0.1.0",
    description="Autonomous AI DevOps Engineer"
)

@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "debug": settings.DEBUG,
    }
    
app.include_router(api_router)