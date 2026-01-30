import asyncio
import websockets
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LocalBridge")

# Connected clients
clients = set()

async def handler(websocket, path):
    """
    Handles WebSocket connections from local Kiosk UI.
    """
    logger.info(f"Client connected: {websocket.remote_address}")
    clients.add(websocket)
    
    try:
        # Send initial status
        await websocket.send(json.dumps({
            "type": "status",
            "data": {
                "online": False,
                "mode": "offline_guest",
                "message": "Connected to Local Bridge"
            }
        }))
        
        async for message in websocket:
            try:
                data = json.loads(message)
                logger.info(f"Received: {data}")
                
                # Echo logic or handle offline transactions here
                if data.get("type") == "deposit":
                    # Store to local DB (TODO)
                    # Respond success
                    await websocket.send(json.dumps({
                        "type": "deposit_ack",
                        "status": "stored_locally"
                    }))
                    
            except json.JSONDecodeError:
                logger.error("Invalid JSON received")
                
    except websockets.exceptions.ConnectionClosed:
        logger.info("Client disconnected")
    finally:
        clients.remove(websocket)

async def start_server():
    server = await websockets.serve(handler, "localhost", 8002)
    logger.info("Local WebSocket Bridge started on ws://localhost:8002")
    await server.wait_closed()

if __name__ == "__main__":
    try:
        asyncio.run(start_server())
    except KeyboardInterrupt:
        pass
