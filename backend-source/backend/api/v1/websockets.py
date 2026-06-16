from fastapi import APIRouter, WebSocket, Depends
from backend.core.websocket_manager import manager
from backend.core.security import get_current_user, User

router = APIRouter()

@router.websocket("/ws/gerencia")
async def websocket_gerencia(websocket: WebSocket, user: User = Depends(get_current_user)):
    if user.role != "gerencia":
        await websocket.close()
        return
    await manager.connect("gerencia", websocket)
    try:
        while True:
            await websocket.receive_text()  # Mantener conexión
    except Exception:
        manager.disconnect("gerencia", websocket)
