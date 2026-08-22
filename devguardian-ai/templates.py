from pathlib import Path

# ==========================================================
# DevGuardian AI Project Structure Generator
# ==========================================================

PROJECT_ROOT = Path.cwd()

folders = [
    "app",
    "app/api",
    "app/core",
    "app/services",
    "app/agents",
    "app/db",
]

files = {
    "app/__init__.py": '''"""
DevGuardian AI Application Package
"""
''',

    "app/main.py": '''from fastapi import FastAPI
from app.api.router import api_router

app = FastAPI(
    title="DevGuardian AI",
    version="0.1.0"
)

app.include_router(api_router)


@app.get("/")
def root():
    return {
        "message": "Welcome to DevGuardian AI 🚀"
    }
''',

    "app/api/__init__.py": '''"""
API Package
"""
''',

    "app/api/health.py": '''from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health():
    return {
        "status": "ok"
    }
''',

    "app/api/webhook.py": '''from fastapi import APIRouter

router = APIRouter()


@router.post("/webhook")
async def github_webhook():
    return {
        "message": "Webhook endpoint created"
    }
''',

    "app/api/router.py": '''from fastapi import APIRouter

from app.api.health import router as health_router
from app.api.webhook import router as webhook_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(webhook_router)
''',

    "app/core/__init__.py": '''"""
Core Package
"""
''',

    "app/services/__init__.py": '''"""
Services Package
"""
''',

    "app/agents/__init__.py": '''"""
Agents Package
"""
''',

    "app/db/__init__.py": '''"""
Database Package
"""
'''
}


def create_structure():
    print("=" * 50)
    print("Creating DevGuardian AI Project Structure")
    print("=" * 50)

    for folder in folders:
        path = PROJECT_ROOT / folder
        path.mkdir(parents=True, exist_ok=True)
        print(f"📁 {folder}")

    for file_path, content in files.items():
        file = PROJECT_ROOT / file_path

        if not file.exists():
            file.write_text(content, encoding="utf-8")
            print(f"📄 {file_path}")
        else:
            print(f"⏩ Skipped {file_path}")

    print("\n✅ Project structure created successfully!")


if __name__ == "__main__":
    create_structure()