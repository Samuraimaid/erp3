from fastapi import WebSocket
from typing import Dict, List

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, role: str, websocket: WebSocket):
        await websocket.accept()
        if role not in self.active_connections:
            self.active_connections[role] = []
        self.active_connections[role].append(websocket)

    def disconnect(self, role: str, websocket: WebSocket):
        if role in self.active_connections:
            self.active_connections[role].remove(websocket)
            if not self.active_connections[role]:
                del self.active_connections[role]

    async def send_to_role(self, role: str, message: dict):
        if role in self.active_connections:
            for ws in self.active_connections[role]:
                await ws.send_json(message)

manager = WebSocketManager()
