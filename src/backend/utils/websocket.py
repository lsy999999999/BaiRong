from fastapi import WebSocket
from typing import Dict, List, Set
from loguru import logger

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, env_name: str):
        await websocket.accept()
        if env_name not in self.active_connections:
            self.active_connections[env_name] = set()
        self.active_connections[env_name].add(websocket)
        logger.info(f"New WebSocket connection for environment {env_name}")

    def disconnect(self, websocket: WebSocket, env_name: str):
        if env_name in self.active_connections:
            self.active_connections[env_name].discard(websocket)
            logger.info(f"WebSocket disconnected for environment {env_name}")

    async def close_websocket_by_env_name(self,env_name:str):
        if env_name in self.active_connections:
            websockets = self.active_connections.pop(env_name)
            for websocket in websockets:
                await websocket.close(code=1000, reason="Normal closure")

    async def broadcast_event(self, env_name: str, event: dict):
        """Broadcast an event to all connected clients for a specific environment"""
        if env_name in self.active_connections:
            disconnected_websockets = set()

            for websocket in self.active_connections[env_name]:
                try:
                    await websocket.send_json(event)
                except Exception as e:
                    logger.error(f"Error sending message to WebSocket: {str(e)}")
                    disconnected_websockets.add(websocket)

            # Clean up disconnected websockets
            for websocket in disconnected_websockets:
                self.disconnect(websocket, env_name)

    def has_active_connections(self, env_name: str) -> bool:
        """Check if there are any active WebSocket connections for the environment"""
        return (
            env_name in self.active_connections
            and len(self.active_connections[env_name]) > 0
        )


# Initialize the connection manager
connection_manager = ConnectionManager() 
