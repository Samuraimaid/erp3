from backend.models.approval_request import ApprovalRequestModel
from backend.db.session import get_collection
from backend.services.venta_service import update_venta_status, generate_token_autorizacion
from fastapi import HTTPException
from datetime import datetime
from typing import Any
from backend.core.security import verify_manager_pin

COLLECTION = "approval_requests"

def create_approval_request(data) -> ApprovalRequestModel:
    collection = get_collection(COLLECTION)
    approval = ApprovalRequestModel(**data.dict())
    collection.insert_one(approval.model_dump(by_alias=True))
    return approval

def get_approval_request_by_id(approval_id: str) -> ApprovalRequestModel:
    collection = get_collection(COLLECTION)
    doc = collection.find_one({"_id": approval_id})
    if not doc:
        raise HTTPException(404, "Solicitud no encontrada")
    return ApprovalRequestModel(**doc)

def resolve_approval_request(approval_id: str, data: Any, user: Any):
    collection = get_collection(COLLECTION)
    approval = get_approval_request_by_id(approval_id)
    if approval.status != "pending":
        raise HTTPException(400, "Ya resuelta")
    if not verify_manager_pin(user.id, data.pin):
        raise HTTPException(403, "PIN incorrecto o no enviado")
    update = {
        "status": data.status,
        "resolved_at": datetime.utcnow(),
        "resolved_by": user.id
    }
    token = None
    if data.status == "approved":
        update_venta_status(approval.sale_id, "APPROVED")
        token = generate_token_autorizacion(approval.sale_id)
        update["token_autorizacion"] = token
    collection.update_one({"_id": approval_id}, {"$set": update})
    return {"status": data.status, "token_autorizacion": token}
