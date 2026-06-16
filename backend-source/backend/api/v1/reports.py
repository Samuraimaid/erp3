from fastapi import APIRouter, Depends, HTTPException, Response
from backend.core.security import get_current_user, User
from backend.db.session import get_collection
from datetime import datetime
from bson import ObjectId
import csv
from io import StringIO

router = APIRouter(prefix="/reports", tags=["reports"])

# Decorador de seguridad

def only_manager_or_admin(user: User = Depends(get_current_user)):
    if user.role not in ("gerencia", "admin"):
        raise HTTPException(403, "Acceso restringido a gerencia o admin")
    return user

@router.get("/audit-summary")
def audit_summary(user: User = Depends(only_manager_or_admin)):
    sales = get_collection("sales")
    pipeline = [
        {"$facet": {
            "descuentos_tarjeta": [
                {"$match": {"payment_method": "Tarjeta"}},
                {"$group": {"_id": None, "total": {"$sum": "$discount_amount"}}}
            ],
            "ventas_status": [
                {"$group": {"_id": "$status", "count": {"$sum": 1}}}
            ],
            "retorno_inventario": [
                {"$unwind": "$products"},
                {"$match": {"products.destino": {"$in": ["Garantía", "Merma"]}}},
                {"$group": {"_id": "$products.destino", "total": {"$sum": {"$multiply": ["$products.cantidad", "$products.precio"]}}}}
            ]
        }}
    ]
    result = list(sales.aggregate(pipeline))[0]
    total_descuentos = result["descuentos_tarjeta"][0]["total"] if result["descuentos_tarjeta"] else 0
    status_counts = {r["_id"]: r["count"] for r in result["ventas_status"]}
    retorno = {r["_id"]: r["total"] for r in result["retorno_inventario"]}
    return {
        "kpis": {
            "totalDescuentos": total_descuentos * 0.04,  # comisión bancaria
            "tasaAnulacion": (status_counts.get("anulada", 0) / max(1, sum(status_counts.values()))) * 100,
            "retornoInventario": {
                "merma": retorno.get("Merma", 0),
                "garantia": retorno.get("Garantía", 0),
                "stock": retorno.get("Stock", 0),
            },
        }
    }

@router.get("/root-causes")
def root_causes(user: User = Depends(only_manager_or_admin)):
    approvals = get_collection("approval_requests")
    pipeline = [
        {"$group": {"_id": "$action_reason", "value": {"$sum": 1}}},
        {"$project": {"name": "$_id", "value": 1, "_id": 0}}
    ]
    causas = list(approvals.aggregate(pipeline))
    return {"causas": causas}

@router.get("/staff-performance")
def staff_performance(user: User = Depends(only_manager_or_admin)):
    approvals = get_collection("approval_requests")
    users = get_collection("users")
    pipeline = [
        {"$group": {"_id": {"cajero_id": "$cajero_id", "gerente": "$resolved_by"}, "count": {"$sum": 1}}},
        {"$group": {"_id": "$_id.cajero_id", "solicitudes": {"$sum": "$count"}, "gerentes": {"$push": {"gerente": "$_id.gerente", "count": "$count"}}}},
        {"$project": {
            "cajero_id": "$_id",
            "solicitudes": 1,
            "gerente": {"$arrayElemAt": [
                {"$slice": [
                    {"$filter": {
                        "input": "$gerentes",
                        "as": "g",
                        "cond": {"$ne": ["$$g.gerente", None]}
                    }}, 1
                ]}, 0
            ]}
        }}
    ]
    tabla = list(approvals.aggregate(pipeline))
    # Enriquecer con nombre de cajero
    for row in tabla:
        user_doc = users.find_one({"_id": ObjectId(row["cajero_id"])})
        row["cajero"] = user_doc["name"] if user_doc else row["cajero_id"]
        row["gerente"] = row["gerente"]["gerente"] if row["gerente"] else "-"
    return {"tabla": tabla}

@router.get("/export-csv")
def export_csv(user: User = Depends(only_manager_or_admin)):
    approvals = get_collection("approval_requests")
    now = datetime.utcnow()
    month_start = datetime(now.year, now.month, 1)
    cursor = approvals.find({"created_at": {"$gte": month_start}})
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Folio Venta", "Cajero", "Tipo", "Monto", "Justificación", "Status", "Fecha", "Gerente"])
    for doc in cursor:
        writer.writerow([
            doc.get("sale_id"),
            doc.get("cajero_id"),
            doc.get("tipo"),
            doc.get("monto_afectado"),
            doc.get("justificacion"),
            doc.get("status"),
            doc.get("created_at"),
            doc.get("resolved_by", "")
        ])
    output.seek(0)
    return Response(content=output.read(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=reporte_incidencias.csv"})
