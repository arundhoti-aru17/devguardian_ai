from fastapi import FastAPI

from app.api.router import api_router

app = FastAPI(
    title="DevGuardian AI",
    version="0.1.0",
    description="Autonomous AI DevOps Engineer"
)

app.include_router(api_router)