from __future__ import annotations

from datetime import datetime, timezone
import uuid
from typing import Any, Dict, Optional


class AuditService:
    def __init__(self, db, logger):
        self.db = db
        self.logger = logger

    async def log_role_change(
        self,
        promoter: Optional[str],
        target_email: str,
        previous_role: Optional[str],
        new_role: str,
        reason: str = "role_change",
        source: str = "api",
    ):
        """Insert a role change audit record into `role_changes` collection."""
        try:
            await self.db.role_changes.insert_one(
                {
                    "promoter": promoter or "system",
                    "target_email": target_email,
                    "previous_role": previous_role,
                    "new_role": new_role,
                    "reason": reason,
                    "source": source,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
        except Exception:
            self.logger.exception("Failed to write role change audit record")

    async def log_pin_auth_attempt(
        self,
        user_id: Optional[str],
        ip: str,
        success: bool,
        reason: str = "pin_login",
    ):
        """Record a PIN auth attempt for auditing and security monitoring."""
        try:
            await self.db.pin_auth_logs.insert_one(
                {
                    "user_id": user_id,
                    "ip": ip,
                    "success": bool(success),
                    "reason": reason,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
        except Exception:
            self.logger.exception("Failed to write pin_auth_logs record")

    async def log_audit_event(
        self,
        action: str,
        actor_id: Optional[str],
        actor_name: Optional[str],
        actor_role: Optional[str],
        entity: str,
        entity_id: Optional[str] = None,
        branch_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Generic audit log for operational actions."""
        try:
            await self.db.audit_logs.insert_one(
                {
                    "action": action,
                    "actor_id": actor_id,
                    "actor_name": actor_name,
                    "actor_role": actor_role,
                    "entity": entity,
                    "entity_id": entity_id,
                    "branch_id": branch_id,
                    "metadata": metadata or {},
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
        except Exception:
            self.logger.exception("Failed to write audit log record")

    async def log_inventory_movement(
        self,
        *,
        product_id: str,
        warehouse_id: str,
        quantity_change: int,
        reason: str,
        actor,
        branch_id: Optional[str] = None,
        reference_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Record inventory movement for traceability."""
        try:
            await self.db.inventory_movements.insert_one(
                {
                    "movement_id": f"mov_{uuid.uuid4().hex[:10]}",
                    "product_id": product_id,
                    "warehouse_id": warehouse_id,
                    "quantity_change": int(quantity_change),
                    "reason": reason,
                    "reference_id": reference_id,
                    "actor_id": actor.user_id,
                    "actor_name": actor.name,
                    "actor_role": actor.role,
                    "branch_id": branch_id or actor.branch_id,
                    "metadata": metadata or {},
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
            )
        except Exception:
            self.logger.exception("Failed to write inventory movement")
