from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from backend.models.approval_request import ApprovalRequestModel
from backend.services.approval_service import (
    create_approval_request,
    resolve_approval_request,
)
from backend.core.security import get_current_user, User
from backend.core.websocket_manager import manager

router = APIRouter(prefix="/approvals", tags=["approvals"])

class ApprovalRequestIn(BaseModel):
    sale_id: str
    cajero_id: str
    tipo: str
    monto_afectado: float
    justificacion: str

@router.post("/request", response_model=ApprovalRequestModel)
async def request_approval(data: ApprovalRequestIn, user: User = Depends(get_current_user)):
    approval = create_approval_request(data)
    await manager.send_to_role("gerencia", {
        "type": "approval_request",
        "approval_id": approval.id,
        "data": approval.model_dump(by_alias=True)
    })
    return approval

class ApprovalResolveIn(BaseModel):
    status: str  # "approved" or "rejected"
    pin: str
    motivo: str = ""

@router.patch("/resolve/{approval_id}")
def resolve_approval(
    approval_id: str,
    data: ApprovalResolveIn,
    user: User = Depends(get_current_user)
):
    if user.role != "gerencia":
        raise HTTPException(status_code=403, detail="Solo gerencia puede resolver solicitudes")
    # PIN se verifica en el servicio
    result = resolve_approval_request(approval_id, data, user)
    return result
