from fastapi import APIRouter

from app.api.health import router as health_router
from app.api.webhook import router as webhook_router
from app.api.incidents import router as incidents_router


api_router = APIRouter(prefix="/api/v1")


# =========================================================
# HEALTH
# =========================================================

api_router.include_router(
    health_router,
    tags=["Health"]
)


# =========================================================
# GITHUB WEBHOOKS
# =========================================================

api_router.include_router(
    webhook_router,
    tags=["GitHub Webhooks"]
)


# =========================================================
# INCIDENTS
# =========================================================

api_router.include_router(
    incidents_router,
    tags=["Incidents"]
)