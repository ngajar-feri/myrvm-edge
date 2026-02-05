"""
ws_local.py - Local WebSocket Bridge for Kiosk UI

Enhanced version that handles offline deposits by storing them
to local SQLite database when the Edge device is in offline mode.
"""

import asyncio
import websockets
import json
import logging
from typing import Set

# Import offline handling modules
from ..services.local_db import get_local_db
from ..services.offline_mode import get_offline_controller, EdgeMode

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LocalBridge")

# Connected clients
clients: Set[websockets.WebSocketServerProtocol] = set()


async def broadcast_status():
    """Broadcast current status to all connected clients."""
    if not clients:
        return
    
    controller = get_offline_controller()
    db = get_local_db()
    
    status_msg = json.dumps({
        "type": "status",
        "data": {
            "online": controller.is_online(),
            "mode": controller.get_current_mode().value,
            "pending_sync_count": db.get_pending_count(),
            "message": "Connected to Local Bridge"
        }
    })
    
    await asyncio.gather(
        *[client.send(status_msg) for client in clients],
        return_exceptions=True
    )


async def handler(websocket, path):
    """
    Handles WebSocket connections from local Kiosk UI.
    
    Supports:
    - Status broadcasting (online/offline mode)
    - Offline deposit handling (stores to SQLite)
    - Transaction acknowledgment
    """
    logger.info(f"Client connected: {websocket.remote_address}")
    clients.add(websocket)
    
    controller = get_offline_controller()
    db = get_local_db()
    
    try:
        # Send initial status
        await websocket.send(json.dumps({
            "type": "status",
            "data": {
                "online": controller.is_online(),
                "mode": controller.get_current_mode().value,
                "pending_sync_count": db.get_pending_count(),
                "message": "Connected to Local Bridge"
            }
        }))
        
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get("type")
                logger.info(f"Received: {msg_type}")
                
                # ==================== Deposit Handling ====================
                if msg_type == "deposit":
                    items = data.get("items", [])
                    
                    if controller.is_offline():
                        # Store offline deposit
                        if not controller.has_system_donation_user_id():
                            await websocket.send(json.dumps({
                                "type": "deposit_error",
                                "error": "System not initialized - please wait for server connection",
                                "code": "NO_USER_ID"
                            }))
                            continue
                        
                        # Set user_id in local_db from controller
                        db.set_system_donation_user_id(controller.get_system_donation_user_id())
                        
                        # Create offline transaction
                        session_id = db.create_offline_transaction(items)
                        
                        if session_id:
                            await websocket.send(json.dumps({
                                "type": "deposit_ack",
                                "status": "stored_locally",
                                "session_id": session_id,
                                "message": "Transaction saved. Will sync when online."
                            }))
                            
                            # Broadcast updated pending count
                            await broadcast_status()
                        else:
                            await websocket.send(json.dumps({
                                "type": "deposit_error",
                                "error": "Failed to store transaction locally",
                                "code": "STORAGE_FAILED"
                            }))
                    else:
                        # Online mode - should go through server, not local bridge
                        await websocket.send(json.dumps({
                            "type": "deposit_error",
                            "error": "Device is online - use server endpoint",
                            "code": "USE_SERVER"
                        }))
                
                # ==================== Status Request ====================
                elif msg_type == "get_status":
                    await websocket.send(json.dumps({
                        "type": "status",
                        "data": controller.get_status()
                    }))
                
                # ==================== Pending Count ====================
                elif msg_type == "get_pending":
                    await websocket.send(json.dumps({
                        "type": "pending_info",
                        "count": db.get_pending_count()
                    }))
                
                # ==================== Ping/Pong ====================
                elif msg_type == "ping":
                    await websocket.send(json.dumps({
                        "type": "pong",
                        "timestamp": data.get("timestamp")
                    }))
                
                else:
                    logger.warning(f"Unknown message type: {msg_type}")
                    
            except json.JSONDecodeError:
                logger.error("Invalid JSON received")
                await websocket.send(json.dumps({
                    "type": "error",
                    "error": "Invalid JSON format"
                }))
                
    except websockets.exceptions.ConnectionClosed:
        logger.info("Client disconnected")
    finally:
        clients.discard(websocket)


async def start_local_bridge(port: int = 8002):
    """
    Start the Local WebSocket Bridge server.
    
    Args:
        port: Port to listen on (default: 8002)
    """
    server = await websockets.serve(handler, "0.0.0.0", port)
    logger.info(f"Local WebSocket Bridge started on ws://0.0.0.0:{port}")
    
    # Register mode change callback to broadcast status
    controller = get_offline_controller()
    controller.on_mode_change(lambda old, new, reason: asyncio.create_task(broadcast_status()))
    
    await server.wait_closed()


if __name__ == "__main__":
    try:
        asyncio.run(start_local_bridge())
    except KeyboardInterrupt:
        pass
