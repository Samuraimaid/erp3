from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional
import uuid
import csv
from io import BytesIO, StringIO

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import pandas as pd


def get_inventory_router(db, audit_service, require_auth, require_roles, InventoryUpdate):
    router = APIRouter()

    WAREHOUSE_SPANISH_FALLBACK = {
        "wh_main": "Bodega Central",
        "wh_north1": "Bodega Norte 1",
        "wh_north2": "Bodega Norte 2",
        "wh_south1": "Bodega Sur 1",
        "wh_south2": "Bodega Sur 2",
        "wh_east": "Bodega Este",
        "wh_west": "Bodega Oeste",
        "wh_express": "Bodega Express",
    }

    def _can_view_all_movements(role: Optional[str]) -> bool:
        return role in {"gerencia", "supervisor", "recursos_humanos", "programador"}

    async def _fetch_inventory_movements(
        user,
        product_id: Optional[str] = None,
        warehouse_id: Optional[str] = None,
        branch_id: Optional[str] = None,
        actor_id: Optional[str] = None,
        reason: Optional[str] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
        limit: int = 200,
    ):
        query: Dict[str, Any] = {}
        if product_id:
            query["product_id"] = product_id
        if reason:
            query["reason"] = reason
        if branch_id:
            query["branch_id"] = branch_id
        if actor_id:
            query["actor_id"] = actor_id

        if not _can_view_all_movements(user.role):
            if user.warehouse_id:
                query["warehouse_id"] = user.warehouse_id
            elif user.branch_id:
                query["branch_id"] = user.branch_id
        elif warehouse_id:
            query["warehouse_id"] = warehouse_id

        if start or end:
            query["created_at"] = {}
            if start:
                query["created_at"]["$gte"] = start
            if end:
                query["created_at"]["$lte"] = end

        movements = (
            await db.inventory_movements.find(query, {"_id": 0})
            .sort("created_at", -1)
            .to_list(limit)
        )
        return movements

    @router.get("/inventory")
    async def get_inventory(
        request: Request, warehouse_id: Optional[str] = None, low_stock: bool = False
    ):
        user = await require_auth(request)
        query: dict[str, Any] = {}
        if user.role == "bodegas" and user.warehouse_id:
            query["warehouse_id"] = user.warehouse_id
        elif warehouse_id:
            query["warehouse_id"] = warehouse_id
        elif user.warehouse_id:
            query["warehouse_id"] = user.warehouse_id

        inventory = await db.inventory.find(query, {"_id": 0}).to_list(5000)

        if low_stock:
            inventory = [i for i in inventory if i["quantity"] <= i["min_stock"]]

        # Enrich with product data
        for item in inventory:
            product = await db.products.find_one(
                {"product_id": item["product_id"]}, {"_id": 0}
            )
            if product:
                item["product"] = product

        return inventory

    @router.get("/inventory/warehouses")
    async def get_inventory_warehouses(request: Request):
        await require_auth(request)
        warehouses = await db.warehouses.find(
            {"is_active": True},
            {"_id": 0, "warehouse_id": 1, "name": 1, "branch_id": 1},
        ).to_list(300)
        return warehouses

    @router.get("/inventory/movements")
    async def get_inventory_movements(
        request: Request,
        product_id: Optional[str] = None,
        warehouse_id: Optional[str] = None,
        branch_id: Optional[str] = None,
        actor_id: Optional[str] = None,
        reason: Optional[str] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
        limit: int = 200,
    ):
        user = await require_auth(request)
        movements = await _fetch_inventory_movements(
            user=user,
            product_id=product_id,
            warehouse_id=warehouse_id,
            branch_id=branch_id,
            actor_id=actor_id,
            reason=reason,
            start=start,
            end=end,
            limit=limit,
        )
        return movements

    @router.get("/inventory/movements/export")
    async def export_inventory_movements(
        request: Request,
        format: str = "csv",
        product_id: Optional[str] = None,
        warehouse_id: Optional[str] = None,
        branch_id: Optional[str] = None,
        actor_id: Optional[str] = None,
        reason: Optional[str] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
        limit: int = 5000,
    ):
        user = await require_auth(request)
        fmt = (format or "csv").strip().lower()
        if fmt not in {"csv", "excel", "pdf"}:
            raise HTTPException(status_code=400, detail="Formato no soportado")

        movements = await _fetch_inventory_movements(
            user=user,
            product_id=product_id,
            warehouse_id=warehouse_id,
            branch_id=branch_id,
            actor_id=actor_id,
            reason=reason,
            start=start,
            end=end,
            limit=limit,
        )

        warehouse_ids = sorted(
            {
                str(movement.get("warehouse_id"))
                for movement in movements
                if movement.get("warehouse_id")
            }
        )
        warehouses_map: Dict[str, str] = {}
        if warehouse_ids:
            warehouses = await db.warehouses.find(
                {"warehouse_id": {"$in": warehouse_ids}},
                {"_id": 0, "warehouse_id": 1, "name": 1},
            ).to_list(len(warehouse_ids) + 20)
            warehouses_map = {
                str(item.get("warehouse_id")): str(item.get("name"))
                for item in warehouses
                if item.get("warehouse_id") and item.get("name")
            }

        def warehouse_label(warehouse_id: Optional[str]) -> str:
            if not warehouse_id:
                return "-"
            return (
                warehouses_map.get(warehouse_id)
                or WAREHOUSE_SPANISH_FALLBACK.get(warehouse_id)
                or warehouse_id
            )

        export_rows = []
        for movement in movements:
            warehouse_id_value = movement.get("warehouse_id")
            export_rows.append(
                {
                    "Fecha": movement.get("created_at"),
                    "Producto": movement.get("product_id"),
                    "Bodega": warehouse_label(warehouse_id_value),
                    "Motivo": movement.get("reason"),
                    "Cantidad": movement.get("quantity_change"),
                    "Usuario": movement.get("actor_name") or movement.get("actor_id"),
                    "Referencia": movement.get("reference_id"),
                }
            )

        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

        if fmt == "csv":
            output = StringIO()
            writer = csv.DictWriter(
                output,
                fieldnames=["Fecha", "Producto", "Bodega", "Motivo", "Cantidad", "Usuario", "Referencia"],
            )
            writer.writeheader()
            writer.writerows(export_rows)
            bytes_data = output.getvalue().encode("utf-8-sig")
            return StreamingResponse(
                BytesIO(bytes_data),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=kardex_{ts}.csv"},
            )

        if fmt == "excel":
            df = pd.DataFrame(export_rows)
            excel_buffer = BytesIO()
            with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="Kardex")
            excel_buffer.seek(0)
            return StreamingResponse(
                excel_buffer,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename=kardex_{ts}.xlsx"},
            )

        # pdf
        pdf_buffer = BytesIO()
        pdf = canvas.Canvas(pdf_buffer, pagesize=letter)
        width, height = letter
        y = height - 36
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(30, y, "Kardex de Inventario")
        y -= 22
        pdf.setFont("Helvetica", 8)
        pdf.drawString(30, y, "Fecha")
        pdf.drawString(145, y, "Producto")
        pdf.drawString(250, y, "Bodega")
        pdf.drawString(330, y, "Motivo")
        pdf.drawString(430, y, "Cant")
        pdf.drawString(475, y, "Usuario")
        y -= 10
        pdf.line(30, y, width - 30, y)
        y -= 12

        for row in export_rows:
            if y < 36:
                pdf.showPage()
                y = height - 36
                pdf.setFont("Helvetica", 8)
            pdf.drawString(30, y, str(row.get("Fecha") or "")[:18])
            pdf.drawString(145, y, str(row.get("Producto") or "")[:20])
            pdf.drawString(250, y, str(row.get("Bodega") or "")[:12])
            pdf.drawString(330, y, str(row.get("Motivo") or "")[:16])
            pdf.drawRightString(462, y, str(row.get("Cantidad") or ""))
            pdf.drawString(475, y, str(row.get("Usuario") or "")[:16])
            y -= 11

        pdf.save()
        pdf_buffer.seek(0)
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=kardex_{ts}.pdf"},
        )

    @router.post("/inventory/warranty-requests")
    async def create_warranty_request(payload: Dict[str, Any], request: Request):
        user = await require_auth(request)

        data = payload or {}
        product_id = data.get("product_id")
        warehouse_id = data.get("warehouse_id")
        scope = (data.get("scope") or "partial").strip().lower()
        affected_quantity = int(data.get("affected_quantity") or 0)
        replacement_quantity = int(data.get("replacement_quantity") or 0)
        notes = data.get("notes")

        if not product_id or not warehouse_id:
            raise HTTPException(status_code=400, detail="product_id y warehouse_id son requeridos")
        if scope not in {"partial", "total"}:
            raise HTTPException(status_code=400, detail="scope debe ser partial o total")
        if affected_quantity <= 0 or replacement_quantity <= 0:
            raise HTTPException(status_code=400, detail="Cantidades deben ser mayores a 0")
        if replacement_quantity > affected_quantity:
            raise HTTPException(status_code=400, detail="replacement_quantity no puede exceder affected_quantity")

        request_id = f"wr_{uuid.uuid4().hex[:10]}"
        doc = {
            "request_id": request_id,
            "product_id": product_id,
            "warehouse_id": warehouse_id,
            "scope": scope,
            "affected_quantity": affected_quantity,
            "replacement_quantity": replacement_quantity,
            "notes": notes,
            "status": "pending",
            "requested_by": user.user_id,
            "requested_by_name": user.name,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.inventory_warranty_requests.insert_one(doc)

        await audit_service.log_audit_event(
            action="inventory_warranty_request",
            actor_id=user.user_id,
            actor_name=user.name,
            actor_role=user.role,
            entity="warranty_request",
            entity_id=request_id,
            branch_id=user.branch_id,
            metadata={
                "product_id": product_id,
                "warehouse_id": warehouse_id,
                "scope": scope,
                "affected_quantity": affected_quantity,
                "replacement_quantity": replacement_quantity,
            },
        )

        return {"message": "Solicitud de garantía creada", "request_id": request_id}

    @router.get("/inventory/warranty-requests")
    async def get_warranty_requests(request: Request, status: Optional[str] = None):
        await require_auth(request)
        query: Dict[str, Any] = {}
        if status:
            query["status"] = status
        requests = (
            await db.inventory_warranty_requests.find(query, {"_id": 0})
            .sort("created_at", -1)
            .to_list(300)
        )
        return requests

    @router.put("/inventory/warranty-requests/{request_id}/approve")
    async def approve_warranty_request(request_id: str, request: Request):
        user = await require_roles(request, ["gerencia", "supervisor", "bodegas"])
        req = await db.inventory_warranty_requests.find_one({"request_id": request_id})
        if not req:
            raise HTTPException(status_code=404, detail="Solicitud de garantía no encontrada")
        if req.get("status") != "pending":
            raise HTTPException(status_code=400, detail="Solicitud ya procesada")

        product_id = req.get("product_id")
        warehouse_id = req.get("warehouse_id")
        replacement_quantity = int(req.get("replacement_quantity") or 0)

        inventory = await db.inventory.find_one({"product_id": product_id, "warehouse_id": warehouse_id})
        if not inventory or int(inventory.get("quantity") or 0) < replacement_quantity:
            raise HTTPException(status_code=400, detail="Stock insuficiente para reposición de garantía")

        await db.inventory.update_one(
            {"product_id": product_id, "warehouse_id": warehouse_id},
            {
                "$inc": {"quantity": -replacement_quantity},
                "$set": {"last_updated": datetime.now(timezone.utc).isoformat()},
            },
        )

        await audit_service.log_inventory_movement(
            product_id=str(product_id),
            warehouse_id=str(warehouse_id),
            quantity_change=-replacement_quantity,
            reason="warranty_replacement_out",
            actor=user,
            branch_id=user.branch_id,
            reference_id=request_id,
            metadata={
                "scope": req.get("scope"),
                "affected_quantity": req.get("affected_quantity"),
                "replacement_quantity": replacement_quantity,
            },
        )

        await db.inventory_warranty_requests.update_one(
            {"request_id": request_id},
            {
                "$set": {
                    "status": "approved",
                    "approved_by": user.user_id,
                    "approved_by_name": user.name,
                    "approved_at": datetime.now(timezone.utc).isoformat(),
                }
            },
        )

        return {"message": "Solicitud de garantía aprobada"}

    @router.put("/inventory/warranty-requests/{request_id}/reject")
    async def reject_warranty_request(request_id: str, request: Request, reason: str = ""):
        user = await require_roles(request, ["gerencia", "supervisor", "bodegas"])
        result = await db.inventory_warranty_requests.update_one(
            {"request_id": request_id, "status": "pending"},
            {
                "$set": {
                    "status": "rejected",
                    "rejected_by": user.user_id,
                    "rejected_by_name": user.name,
                    "rejected_at": datetime.now(timezone.utc).isoformat(),
                    "rejection_reason": reason,
                }
            },
        )
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Solicitud no encontrada o ya procesada")
        return {"message": "Solicitud de garantía rechazada"}

    @router.post("/inventory")
    async def update_inventory(inv_data: InventoryUpdate, request: Request):
        user = await require_roles(request, ["gerencia", "supervisor", "bodegas", "jefe_tienda"])

        if user.role == "bodegas":
            raise HTTPException(
                status_code=403,
                detail="Usuarios de bodega solo pueden agregar stock mediante el flujo de ingreso",
            )

        existing = await db.inventory.find_one(
            {"product_id": inv_data.product_id, "warehouse_id": inv_data.warehouse_id}
        )

        doc = inv_data.model_dump()
        doc["last_updated"] = datetime.now(timezone.utc).isoformat()
        existing_qty = existing.get("quantity", 0) if existing else 0

        if existing:
            await db.inventory.update_one(
                {"product_id": inv_data.product_id, "warehouse_id": inv_data.warehouse_id},
                {"$set": doc},
            )
        else:
            doc["inventory_id"] = f"inv_{uuid.uuid4().hex[:8]}"
            await db.inventory.insert_one(doc)

        await audit_service.log_inventory_movement(
            product_id=inv_data.product_id,
            warehouse_id=inv_data.warehouse_id,
            quantity_change=int(inv_data.quantity) - int(existing_qty),
            reason="manual_update",
            actor=user,
            branch_id=user.branch_id,
            reference_id=doc.get("inventory_id"),
            metadata={"min_stock": inv_data.min_stock},
        )

        await audit_service.log_audit_event(
            action="inventory_update",
            actor_id=user.user_id,
            actor_name=user.name,
            actor_role=user.role,
            entity="inventory",
            entity_id=doc.get("inventory_id"),
            branch_id=user.branch_id,
            metadata={
                "product_id": inv_data.product_id,
                "warehouse_id": inv_data.warehouse_id,
                "quantity": inv_data.quantity,
                "min_stock": inv_data.min_stock,
            },
        )

        return doc

    @router.post("/inventory/add-stock")
    async def add_inventory_stock(
        request: Request,
        product_id: str,
        warehouse_id: str,
        quantity: int,
        min_stock: Optional[int] = None,
    ):
        user = await require_roles(request, ["gerencia", "supervisor", "bodegas", "jefe_tienda"])

        try:
            qty_to_add = int(quantity)
        except Exception:
            qty_to_add = 0
        if qty_to_add <= 0:
            raise HTTPException(status_code=400, detail="La cantidad a agregar debe ser mayor a cero")

        if user.role == "bodegas":
            if not user.warehouse_id:
                raise HTTPException(status_code=400, detail="Usuario de bodega sin bodega asignada")
            if warehouse_id != user.warehouse_id:
                raise HTTPException(status_code=403, detail="Solo puedes agregar stock a tu bodega asignada")

        inventory_filter = {"product_id": product_id, "warehouse_id": warehouse_id}
        existing = await db.inventory.find_one(inventory_filter)
        now_iso = datetime.now(timezone.utc).isoformat()

        if existing:
            update_doc: Dict[str, Any] = {
                "$inc": {"quantity": qty_to_add},
                "$set": {"last_updated": now_iso},
            }
            if min_stock is not None:
                update_doc["$set"]["min_stock"] = max(1, int(min_stock))
            await db.inventory.update_one(inventory_filter, update_doc)
            inventory_id = existing.get("inventory_id")
            updated_quantity = int(existing.get("quantity") or 0) + qty_to_add
        else:
            inventory_id = f"inv_{uuid.uuid4().hex[:8]}"
            initial_min_stock = max(1, int(min_stock or 5))
            updated_quantity = qty_to_add
            await db.inventory.insert_one(
                {
                    "inventory_id": inventory_id,
                    "product_id": product_id,
                    "warehouse_id": warehouse_id,
                    "quantity": updated_quantity,
                    "min_stock": initial_min_stock,
                    "last_updated": now_iso,
                }
            )

        await audit_service.log_inventory_movement(
            product_id=product_id,
            warehouse_id=warehouse_id,
            quantity_change=qty_to_add,
            reason="manual_add_stock",
            actor=user,
            branch_id=user.branch_id,
            reference_id=inventory_id,
            metadata={"min_stock": min_stock},
        )

        return {
            "inventory_id": inventory_id,
            "product_id": product_id,
            "warehouse_id": warehouse_id,
            "quantity": updated_quantity,
            "added": qty_to_add,
        }

    @router.post("/inventory/transfer")
    async def transfer_inventory(
        request: Request,
        product_id: str,
        from_warehouse: str,
        to_warehouse: str,
        quantity: int,
    ):
        user = await require_roles(request, ["gerencia", "supervisor", "bodegas", "jefe_tienda"])

        if user.role == "bodegas":
            if not user.warehouse_id:
                raise HTTPException(status_code=400, detail="Usuario de bodega sin bodega asignada")
            if from_warehouse != user.warehouse_id:
                raise HTTPException(status_code=403, detail="Solo puedes trasladar desde tu bodega asignada")

        # Check source inventory
        source = await db.inventory.find_one(
            {"product_id": product_id, "warehouse_id": from_warehouse}
        )
        if not source or source["quantity"] < quantity:
            raise HTTPException(status_code=400, detail="Insufficient inventory")

        # Update source
        await db.inventory.update_one(
            {"product_id": product_id, "warehouse_id": from_warehouse},
            {
                "$inc": {"quantity": -quantity},
                "$set": {"last_updated": datetime.now(timezone.utc).isoformat()},
            },
        )

        await audit_service.log_inventory_movement(
            product_id=product_id,
            warehouse_id=from_warehouse,
            quantity_change=-int(quantity),
            reason="transfer_out",
            actor=user,
            branch_id=user.branch_id,
            reference_id=None,
            metadata={"to_warehouse": to_warehouse},
        )

        # Update destination
        dest = await db.inventory.find_one(
            {"product_id": product_id, "warehouse_id": to_warehouse}
        )
        if dest:
            await db.inventory.update_one(
                {"product_id": product_id, "warehouse_id": to_warehouse},
                {
                    "$inc": {"quantity": quantity},
                    "$set": {"last_updated": datetime.now(timezone.utc).isoformat()},
                },
            )
        else:
            await db.inventory.insert_one(
                {
                    "inventory_id": f"inv_{uuid.uuid4().hex[:8]}",
                    "product_id": product_id,
                    "warehouse_id": to_warehouse,
                    "quantity": quantity,
                    "min_stock": 5,
                    "last_updated": datetime.now(timezone.utc).isoformat(),
                }
            )

        await audit_service.log_inventory_movement(
            product_id=product_id,
            warehouse_id=to_warehouse,
            quantity_change=int(quantity),
            reason="transfer_in",
            actor=user,
            branch_id=user.branch_id,
            reference_id=None,
            metadata={"from_warehouse": from_warehouse},
        )

        await audit_service.log_audit_event(
            action="inventory_transfer",
            actor_id=user.user_id,
            actor_name=user.name,
            actor_role=user.role,
            entity="inventory_transfer",
            entity_id=None,
            branch_id=user.branch_id,
            metadata={
                "product_id": product_id,
                "from_warehouse": from_warehouse,
                "to_warehouse": to_warehouse,
                "quantity": quantity,
            },
        )

        return {"message": "Transfer completed"}

    @router.post("/inventory/transfer-request")
    async def request_inventory_transfer(
        request: Request,
        product_id: str,
        from_warehouse_id: str,
        to_warehouse_id: str,
        quantity: int = 1,
        reason: str = "",
    ):
        """Request a transfer that requires supervisor approval"""
        user = await require_auth(request)

        # Create transfer request
        transfer_request = {
            "request_id": f"tr_{uuid.uuid4().hex[:8]}",
            "product_id": product_id,
            "from_warehouse_id": from_warehouse_id,
            "to_warehouse_id": to_warehouse_id,
            "quantity": quantity,
            "reason": reason,
            "requested_by": user.user_id,
            "requested_by_name": user.name,
            "status": "pending",  # pending, approved, rejected
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        await db.transfer_requests.insert_one(transfer_request)
        transfer_request.pop("_id", None)

        await audit_service.log_audit_event(
            action="inventory_transfer_request",
            actor_id=user.user_id,
            actor_name=user.name,
            actor_role=user.role,
            entity="transfer_request",
            entity_id=transfer_request["request_id"],
            branch_id=user.branch_id,
            metadata={
                "product_id": product_id,
                "from_warehouse_id": from_warehouse_id,
                "to_warehouse_id": to_warehouse_id,
                "quantity": quantity,
                "reason": reason,
            },
        )

        return {
            "message": "Solicitud de traslado creada",
            "request_id": transfer_request["request_id"],
        }

    @router.get("/inventory/transfer-requests")
    async def get_transfer_requests(request: Request, status: Optional[str] = None):
        """Get all transfer requests (for supervisor/gerencia)"""
        await require_roles(request, ["gerencia", "supervisor"])

        query: dict[str, Any] = {}
        if status:
            query["status"] = status

        requests = (
            await db.transfer_requests.find(query, {"_id": 0})
            .sort("created_at", -1)
            .to_list(100)
        )
        return requests

    @router.put("/inventory/transfer-requests/{request_id}/approve")
    async def approve_transfer_request(request_id: str, request: Request):
        """Approve a transfer request and execute the transfer"""
        user = await require_roles(request, ["gerencia", "supervisor"])

        transfer_req = await db.transfer_requests.find_one({"request_id": request_id})
        if not transfer_req:
            raise HTTPException(status_code=404, detail="Solicitud no encontrada")

        if transfer_req["status"] != "pending":
            raise HTTPException(status_code=400, detail="Solicitud ya procesada")

        # Execute the transfer
        source = await db.inventory.find_one(
            {
                "product_id": transfer_req["product_id"],
                "warehouse_id": transfer_req["from_warehouse_id"],
            }
        )
        if not source or source["quantity"] < transfer_req["quantity"]:
            raise HTTPException(
                status_code=400, detail="Stock insuficiente en bodega origen"
            )

        # Update source
        await db.inventory.update_one(
            {
                "product_id": transfer_req["product_id"],
                "warehouse_id": transfer_req["from_warehouse_id"],
            },
            {"$inc": {"quantity": -transfer_req["quantity"]}},
        )

        await audit_service.log_inventory_movement(
            product_id=transfer_req["product_id"],
            warehouse_id=transfer_req["from_warehouse_id"],
            quantity_change=-int(transfer_req["quantity"]),
            reason="transfer_request_out",
            actor=user,
            branch_id=user.branch_id,
            reference_id=request_id,
            metadata={"to_warehouse": transfer_req["to_warehouse_id"]},
        )

        # Update destination
        dest = await db.inventory.find_one(
            {
                "product_id": transfer_req["product_id"],
                "warehouse_id": transfer_req["to_warehouse_id"],
            }
        )
        if dest:
            await db.inventory.update_one(
                {
                    "product_id": transfer_req["product_id"],
                    "warehouse_id": transfer_req["to_warehouse_id"],
                },
                {"$inc": {"quantity": transfer_req["quantity"]}},
            )
        else:
            await db.inventory.insert_one(
                {
                    "inventory_id": f"inv_{uuid.uuid4().hex[:8]}",
                    "product_id": transfer_req["product_id"],
                    "warehouse_id": transfer_req["to_warehouse_id"],
                    "quantity": transfer_req["quantity"],
                    "min_stock": 5,
                    "last_updated": datetime.now(timezone.utc).isoformat(),
                }
            )

        await audit_service.log_inventory_movement(
            product_id=transfer_req["product_id"],
            warehouse_id=transfer_req["to_warehouse_id"],
            quantity_change=int(transfer_req["quantity"]),
            reason="transfer_request_in",
            actor=user,
            branch_id=user.branch_id,
            reference_id=request_id,
            metadata={"from_warehouse": transfer_req["from_warehouse_id"]},
        )

        # Update request status
        await db.transfer_requests.update_one(
            {"request_id": request_id},
            {
                "$set": {
                    "status": "approved",
                    "approved_by": user.user_id,
                    "approved_by_name": user.name,
                    "approved_at": datetime.now(timezone.utc).isoformat(),
                }
            },
        )

        await audit_service.log_audit_event(
            action="inventory_transfer_approved",
            actor_id=user.user_id,
            actor_name=user.name,
            actor_role=user.role,
            entity="transfer_request",
            entity_id=request_id,
            branch_id=user.branch_id,
            metadata={
                "product_id": transfer_req["product_id"],
                "from_warehouse_id": transfer_req["from_warehouse_id"],
                "to_warehouse_id": transfer_req["to_warehouse_id"],
                "quantity": transfer_req["quantity"],
            },
        )

        return {"message": "Traslado aprobado y ejecutado"}

    @router.put("/inventory/transfer-requests/{request_id}/reject")
    async def reject_transfer_request(request_id: str, request: Request, reason: str = ""):
        """Reject a transfer request"""
        user = await require_roles(request, ["gerencia", "supervisor"])

        result = await db.transfer_requests.update_one(
            {"request_id": request_id, "status": "pending"},
            {
                "$set": {
                    "status": "rejected",
                    "rejected_by": user.user_id,
                    "rejected_by_name": user.name,
                    "rejection_reason": reason,
                    "rejected_at": datetime.now(timezone.utc).isoformat(),
                }
            },
        )

        if result.modified_count == 0:
            raise HTTPException(
                status_code=404, detail="Solicitud no encontrada o ya procesada"
            )

        await audit_service.log_audit_event(
            action="inventory_transfer_rejected",
            actor_id=user.user_id,
            actor_name=user.name,
            actor_role=user.role,
            entity="transfer_request",
            entity_id=request_id,
            branch_id=user.branch_id,
            metadata={"reason": reason},
        )

        return {"message": "Traslado rechazado"}

    return router
