from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import os
import requests
from backend.db.session import get_collection
import pytz
import logging

# Configuración de APScheduler
scheduler = BackgroundScheduler(timezone="America/Mexico_City")

TELEGRAM_WEBHOOK = os.getenv("TELEGRAM_WEBHOOK")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- Utilidades ---
def send_executive_summary(message: str):
    if not TELEGRAM_WEBHOOK or not TELEGRAM_CHAT_ID:
        logging.error("Webhook o Chat ID no configurados")
        return False
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    resp = requests.post(TELEGRAM_WEBHOOK, json=payload)
    return resp.status_code == 200

# --- Tarea programada ---
def weekly_business_sentinel():
    try:
        # 1. Venta total de la semana
        now = datetime.now(pytz.timezone("America/Mexico_City"))
        week_start = now - timedelta(days=now.weekday()+1)
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        sales = get_collection("sales")
        total_venta = sales.aggregate([
            {"$match": {"created_at": {"$gte": week_start}}},
            {"$group": {"_id": None, "total": {"$sum": "$total"}}}
        ])
        total_venta = next(total_venta, {}).get("total", 0)

        # 2. Fuga por comisiones
        audit = requests.get("http://localhost:8001/reports/audit-summary", headers={"Authorization": f"Bearer {os.getenv('SCHEDULER_TOKEN','')}"})
        fuga = audit.json()["kpis"]["totalDescuentos"]

        # 3. Top 3 productos devueltos
        devols = sales.aggregate([
            {"$unwind": "$products"},
            {"$match": {"products.status": "devuelto"}},
            {"$group": {"_id": "$products.nombre", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 3}
        ])
        top_devs = [f"{d['_id']} ({d['count']})" for d in devols]

        # 4. Auditoría de confianza
        perf = requests.get("http://localhost:8001/reports/staff-performance", headers={"Authorization": f"Bearer {os.getenv('SCHEDULER_TOKEN','')}"})
        tabla = perf.json()["tabla"]
        if tabla:
            cajero = max(tabla, key=lambda x: x["solicitudes"])
            gerente = cajero["gerente"]
        else:
            cajero = {"cajero": "-", "solicitudes": 0, "gerente": "-"}
            gerente = "-"

        # Mensaje estructurado
        msg = (
            f"<b>📊 Resumen Ejecutivo Semanal</b>\n"
            f"\n💰 <b>Venta Total:</b> ${total_venta:,.2f}"
            f"\n💳 <b>Fuga por Comisiones:</b> ${fuga:,.2f}"
            f"\n⚠️ <b>Top Devoluciones:</b> {', '.join(top_devs) if top_devs else 'Sin devoluciones'}"
            f"\n👤 <b>Auditoría de Confianza:</b> {cajero['cajero']} ({cajero['solicitudes']} solicitudes), Gerente: {gerente}"
        )
        ok = send_executive_summary(msg)
        # Log en MongoDB
        logs = get_collection("sentinel_logs")
        logs.insert_one({
            "sent_at": now,
            "destinatario": TELEGRAM_CHAT_ID,
            "ok": ok,
            "msg": msg
        })
    except Exception as e:
        logging.exception("Error en WeeklyBusinessSentinel")

# Programar tarea: Domingos 20:00
scheduler.add_job(weekly_business_sentinel, "cron", day_of_week="sun", hour=20, minute=0)
