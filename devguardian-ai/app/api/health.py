from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health():
    return {
        "status": "ok",
        "service": "DevGuardian AI",
        "version": "0.1.0"
    }