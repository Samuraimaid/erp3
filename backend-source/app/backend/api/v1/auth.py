from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.db.session import get_collection
from backend.core.security import verify_cajero_pin
from datetime import datetime, timedelta

router = APIRouter(prefix="/auth", tags=["auth"])

FAILED_ATTEMPTS_LIMIT = 3
BLOCK_TIME_MINUTES = 10

class VerifyPinRequest(BaseModel):
    cajero_id: str
    pin: str
    terminal_id: str = "default"


@router.post("/verify-pin")
def verify_pin(payload: VerifyPinRequest):
    attempts = get_collection("failed_pin_attempts")
    cajero_id = payload.cajero_id
    terminal_id = payload.terminal_id
    block = attempts.find_one({"cajero_id": cajero_id, "terminal_id": terminal_id})
    now = datetime.utcnow()
    if block and block.get("blocked_until") and block["blocked_until"] > now:
        raise HTTPException(403, "Terminal bloqueada por intentos fallidos. Intenta más tarde.")
    if not verify_cajero_pin(cajero_id, payload.pin):
        fail_count = (block["count"] + 1) if block else 1
        update = {"$set": {"count": fail_count, "last": now}}
        if fail_count >= FAILED_ATTEMPTS_LIMIT:
            update["$set"]["blocked_until"] = now + timedelta(minutes=BLOCK_TIME_MINUTES)
            from backend.services.weekly_business_sentinel import send_executive_summary
            send_executive_summary(f"Alerta: PIN incorrecto 3 veces. Cajero: {cajero_id}, Terminal: {terminal_id}")
        attempts.update_one({"cajero_id": cajero_id, "terminal_id": terminal_id}, update, upsert=True)
        raise HTTPException(401, "PIN incorrecto")
    attempts.delete_one({"cajero_id": cajero_id, "terminal_id": terminal_id})
    return {"ok": True}
