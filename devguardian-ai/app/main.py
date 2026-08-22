from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import get_logger
from app.api.router import api_router


logger = get_logger(__name__)


app = FastAPI(
    title="DevGuardian AI",
    version="0.1.0",
    description="Autonomous AI DevOps Engineer"


)


# Log startup information
logger.info(
    f"Starting {settings.APP_NAME} v{settings.APP_VERSION}"
    if hasattr(settings, "APP_VERSION")
    else f"Starting {settings.APP_NAME}"
)
logger.info(f"Environment: {settings.APP_ENV}")
logger.info(f"Debug mode: {settings.DEBUG}")


# Allow the React frontend to communicate with the FastAPI backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "debug": settings.DEBUG,
    }


app.include_router(api_router)