from fastapi import APIRouter

router = APIRouter()


@router.post("/webhook")
async def github_webhook():
    return {
        "message": "GitHub Webhook Received"
    }