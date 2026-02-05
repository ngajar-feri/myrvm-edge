"""
Offline Kiosk App - Local Frontend for Edge Device

This FastAPI application serves a local Kiosk UI when the Edge device
is offline (cannot connect to the server). It provides:
- Donation-only mode UI
- WebSocket connection to Local Bridge (port 8002)
- Automatic switch back when online

Serve on port 8001 (different from setup wizard on 8080)
"""

from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OfflineKiosk")

BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="MyRVM Offline Kiosk")

# Mount static files
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@app.get("/", response_class=HTMLResponse)
async def offline_kiosk(request: Request):
    """
    Serve the offline kiosk UI.
    This is the main page for donation mode when offline.
    """
    return templates.TemplateResponse("offline_kiosk.html", {
        "request": request,
        "local_bridge_url": "ws://localhost:8002",
        "mode": "offline_guest"
    })


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "mode": "offline"}


@app.get("/api/status")
async def get_status():
    """Get current offline kiosk status."""
    try:
        from ..services.offline_mode import get_offline_controller
        from ..services.local_db import get_local_db
        
        controller = get_offline_controller()
        db = get_local_db()
        
        return {
            "mode": controller.get_current_mode().value,
            "is_online": controller.is_online(),
            "pending_transactions": db.get_pending_count()
        }
    except Exception as e:
        return {
            "mode": "offline_guest",
            "is_online": False,
            "error": str(e)
        }


def start_offline_kiosk(port: int = 8001):
    """Start the offline kiosk server."""
    import uvicorn
    logger.info(f"Starting Offline Kiosk on http://0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")


if __name__ == "__main__":
    start_offline_kiosk()
