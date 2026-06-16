from __future__ import annotations

import csv
import hashlib
import io
import os
from datetime import datetime, time, timedelta, timezone
from typing import Any, Dict, List, Optional
import uuid
from zoneinfo import ZoneInfo

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response, StreamingResponse
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def get_human_resources_router(
    db,
    audit_service,
    require_auth,
    require_roles,
    verify_pin_hash,
):
    router = APIRouter(prefix="/hr", tags=["human-resources"])

    HR_ALLOWED_ROLES = ["gerencia", "recursos_humanos", "supervisor", "programador"]
    TECHNICIAN_ROLES = {"instalaciones", "tecnico", "bodegas", "polarizador", "electrico"}
    CLOCK_EVENTS = {"clock_in", "lunch_out", "lunch_in", "clock_out"}
    PIN_LENGTH = 4
    ATTENDANCE_TIMEZONE = ZoneInfo("America/Managua")

    EVENT_LABELS = {
        "clock_in": "Entrada a labores",
        "lunch_out": "Salida a almuerzo",
        "lunch_in": "Entrada de almuerzo",
        "clock_out": "Salida laboral",
    }

    ORDERED_CLOCK_EVENTS = ["clock_in", "lunch_out", "lunch_in", "clock_out"]
    DEFAULT_ATTENDANCE_SETTINGS = {
        "time_format": "12h",
        "kiosk_theme_mode": "system",
        "entry_start": "08:00",
        "entry_tolerance_minutes": 10,
        "late_arrival_deduction_enabled": True,
        "late_arrival_deduction_amount": 50,
        "late_arrival_deduction_currency": "NIO",
        "lunch_out_start": "10:00",
        "lunch_out_end": "16:00",
        "lunch_break_minutes": 40,
        "weekday_shift_end": "17:30",
        "saturday_shift_end": "16:00",
        "anti_double_touch_seconds": 20,
    }

    def now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    def now_local() -> datetime:
        return datetime.now(ATTENDANCE_TIMEZONE)

    def expected_clock_event_for_index(index: int) -> Optional[str]:
        if 0 <= index < len(ORDERED_CLOCK_EVENTS):
            return ORDERED_CLOCK_EVENTS[index]
        return None

    def parse_hhmm(value: str, default_value: str) -> time:
        raw = (value or default_value or "00:00").strip()
        try:
            hour, minute = raw.split(":", 1)
            return time(int(hour), int(minute))
        except Exception:
            default_hour, default_minute = default_value.split(":", 1)
            return time(int(default_hour), int(default_minute))

    def compute_pin_index(pin: str) -> str:
        return hashlib.sha256(pin.encode("utf-8")).hexdigest()

    def get_attendance_pin_hash(user_doc: Dict[str, Any]) -> Optional[str]:
        return user_doc.get("attendance_pin_hash") or user_doc.get("pin_hash")

    async def get_global_attendance_settings() -> Dict[str, Any]:
        doc = await db.hr_attendance_settings.find_one({"scope": "global"}, {"_id": 0})
        if not doc:
            return dict(DEFAULT_ATTENDANCE_SETTINGS)
        merged = dict(DEFAULT_ATTENDANCE_SETTINGS)
        merged.update(doc.get("settings") or {})
        return merged

    async def get_effective_attendance_settings(branch_id: Optional[str] = None) -> Dict[str, Any]:
        settings = await get_global_attendance_settings()
        if branch_id:
            branch_doc = await db.hr_attendance_settings.find_one({"scope": "branch", "branch_id": branch_id}, {"_id": 0})
            if branch_doc and isinstance(branch_doc.get("settings"), dict):
                settings.update(branch_doc.get("settings") or {})
        return settings

    async def get_pin_directory_sync_marker() -> str:
        doc = await db.hr_runtime_meta.find_one({"key": "pin_directory_sync"}, {"_id": 0, "marker": 1})
        marker = (doc or {}).get("marker")
        return str(marker) if marker else ""

    async def touch_pin_directory_sync_marker(actor_user_id: Optional[str] = None) -> str:
        marker = now_iso()
        await db.hr_runtime_meta.update_one(
            {"key": "pin_directory_sync"},
            {
                "$set": {
                    "key": "pin_directory_sync",
                    "marker": marker,
                    "updated_at": marker,
                    "updated_by": actor_user_id or "system",
                }
            },
            upsert=True,
        )
        return marker

    async def write_attendance_settings_audit(
        actor_user_id: str,
        scope: str,
        branch_id: Optional[str],
        before_settings: Dict[str, Any],
        after_settings: Dict[str, Any],
    ) -> None:
        audit_doc = {
            "audit_id": f"cfg_{uuid.uuid4().hex[:10]}",
            "scope": scope,
            "branch_id": branch_id,
            "before": before_settings,
            "after": after_settings,
            "changed_by": actor_user_id,
            "changed_at": now_iso(),
        }
        await db.hr_attendance_settings_audit.insert_one(audit_doc)

    def is_within_window(local_dt: datetime, start_at: time, end_at: time) -> bool:
        current_time = local_dt.time()
        return start_at <= current_time <= end_at

    def get_shift_end_time(local_dt: datetime, settings: Dict[str, Any]) -> time:
        weekday = local_dt.weekday()  # 0=lunes ... 6=domingo
        if weekday == 5:  # sábado
            return parse_hhmm(str(settings.get("saturday_shift_end") or "16:00"), "16:00")
        return parse_hhmm(str(settings.get("weekday_shift_end") or "17:30"), "17:30")

    def validate_clock_window(event_type: str, local_dt: datetime, settings: Dict[str, Any]) -> List[Dict[str, str]]:
        weekday = local_dt.weekday()  # 0=lunes ... 6=domingo
        if weekday == 6:
            raise HTTPException(status_code=400, detail="Domingo no laborable")

        policy_alerts: List[Dict[str, str]] = []

        entry_start = parse_hhmm(str(settings.get("entry_start") or "08:00"), "08:00")
        entry_tolerance = int(settings.get("entry_tolerance_minutes") or 10)
        entry_end_dt = (datetime.combine(local_dt.date(), entry_start) + timedelta(minutes=max(0, entry_tolerance)))
        entry_end = entry_end_dt.time()

        lunch_out_start = parse_hhmm(str(settings.get("lunch_out_start") or "10:00"), "10:00")
        lunch_out_end = parse_hhmm(str(settings.get("lunch_out_end") or "16:00"), "16:00")

        if event_type == "clock_in":
            if local_dt.time() < entry_start:
                raise HTTPException(status_code=400, detail=f"Entrada permitida desde las {entry_start.strftime('%H:%M')}")
            return policy_alerts

        if event_type == "lunch_out":
            if not is_within_window(local_dt, lunch_out_start, lunch_out_end):
                policy_alerts.append(
                    {
                        "incident_type": "lunch_out_outside_window",
                        "description": f"Salida de almuerzo fuera de ventana ({lunch_out_start.strftime('%H:%M')} - {lunch_out_end.strftime('%H:%M')}).",
                    }
                )
            return policy_alerts

        if event_type == "lunch_in":
            shift_end = get_shift_end_time(local_dt, settings)
            if not is_within_window(local_dt, lunch_out_start, shift_end):
                policy_alerts.append(
                    {
                        "incident_type": "lunch_in_outside_window",
                        "description": f"Entrada de almuerzo fuera de ventana (desde {lunch_out_start.strftime('%H:%M')} hasta {shift_end.strftime('%H:%M')}).",
                    }
                )
            return policy_alerts

        if event_type == "clock_out":
            shift_end = get_shift_end_time(local_dt, settings)
            if local_dt.time() < shift_end:
                raise HTTPException(status_code=400, detail=f"Salida laboral permitida desde las {shift_end.strftime('%H:%M')}")
            return policy_alerts

        return policy_alerts

    async def count_user_clock_events_for_local_day(user_id: str, local_dt: datetime) -> int:
        local_start = local_dt.replace(hour=0, minute=0, second=0, microsecond=0)
        local_end = local_start + timedelta(days=1)
        utc_start = local_start.astimezone(timezone.utc).isoformat()
        utc_end = local_end.astimezone(timezone.utc).isoformat()
        query = {
            "user_id": user_id,
            "created_at": {
                "$gte": utc_start,
                "$lt": utc_end,
            },
        }
        return await db.hr_timeclock_events.count_documents(query)

    async def fetch_user_clock_events_for_local_day(user_id: str, local_dt: datetime) -> List[Dict[str, Any]]:
        local_start = local_dt.replace(hour=0, minute=0, second=0, microsecond=0)
        local_end = local_start + timedelta(days=1)
        utc_start = local_start.astimezone(timezone.utc).isoformat()
        utc_end = local_end.astimezone(timezone.utc).isoformat()
        query = {
            "user_id": user_id,
            "created_at": {"$gte": utc_start, "$lt": utc_end},
        }
        return await db.hr_timeclock_events.find(query, {"_id": 0}).sort("created_at", 1).to_list(20)

    async def create_attendance_incident(
        user_id: str,
        user_name: str,
        incident_type: str,
        description: str,
        local_dt: datetime,
        source_clock_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        existing = await db.hr_attendance_incidents.find_one(
            {
                "user_id": user_id,
                "incident_type": incident_type,
                "attendance_date": local_dt.date().isoformat(),
            },
            {"_id": 0},
        )
        if existing:
            return existing

        doc = {
            "incident_id": f"inc_{uuid.uuid4().hex[:10]}",
            "user_id": user_id,
            "user_name": user_name,
            "incident_type": incident_type,
            "description": description,
            "attendance_date": local_dt.date().isoformat(),
            "source_clock_id": source_clock_id,
            "status": "open",
            "created_at": now_iso(),
        }
        await db.hr_attendance_incidents.insert_one(doc)
        return doc

    async def create_user_notification(user_id: str, title: str, message: str, category: str = "attendance") -> None:
        doc = {
            "notification_id": f"ntf_{uuid.uuid4().hex[:10]}",
            "user_id": user_id,
            "title": title,
            "message": message,
            "category": category,
            "read": False,
            "created_at": now_iso(),
        }
        await db.hr_notifications.insert_one(doc)

    async def process_post_clock_rules(
        record: Dict[str, Any],
        settings: Dict[str, Any],
        local_dt: datetime,
        policy_alerts: Optional[List[Dict[str, str]]] = None,
    ) -> None:
        event_type = str(record.get("event_type") or "")
        user_id = str(record.get("user_id") or "")
        user_name = str(record.get("user_name") or user_id)

        for item in (policy_alerts or []):
            incident_type = str(item.get("incident_type") or "outside_policy_window")
            description = str(item.get("description") or "Marcación fuera de política de asistencia.")
            await create_attendance_incident(
                user_id=user_id,
                user_name=user_name,
                incident_type=incident_type,
                description=description,
                local_dt=local_dt,
                source_clock_id=record.get("clock_id"),
            )
            await create_user_notification(
                user_id=user_id,
                title="Marcación fuera de ventana",
                message=description,
            )

        if event_type == "clock_in":
            entry_start = parse_hhmm(str(settings.get("entry_start") or "08:00"), "08:00")
            entry_tolerance = int(settings.get("entry_tolerance_minutes") or 10)
            late_after = (datetime.combine(local_dt.date(), entry_start) + timedelta(minutes=max(0, entry_tolerance))).time()
            if local_dt.time() > late_after:
                late_incident = await create_attendance_incident(
                    user_id=user_id,
                    user_name=user_name,
                    incident_type="late_arrival",
                    description=f"Marcación tardía después de {late_after.strftime('%H:%M')}",
                    local_dt=local_dt,
                    source_clock_id=record.get("clock_id"),
                )
                await create_user_notification(
                    user_id=user_id,
                    title="Marcación tardía registrada",
                    message=f"Tu entrada fue registrada después de {late_after.strftime('%H:%M')}.",
                )

                raw_deduction_enabled = settings.get("late_arrival_deduction_enabled", True)
                if isinstance(raw_deduction_enabled, str):
                    deduction_enabled = raw_deduction_enabled.strip().lower() in {"1", "true", "yes", "si", "on"}
                else:
                    deduction_enabled = bool(raw_deduction_enabled)

                deduction_amount = max(0.0, float(settings.get("late_arrival_deduction_amount") or 0))
                deduction_currency = str(settings.get("late_arrival_deduction_currency") or "NIO").strip().upper() or "NIO"
                incident_id = str((late_incident or {}).get("incident_id") or "")

                if deduction_enabled and deduction_amount > 0 and incident_id:
                    existing_deduction = await db.hr_payroll_adjustments.find_one(
                        {
                            "user_id": user_id,
                            "adjustment_type": "late_arrival_deduction",
                            "reference_type": "attendance_incident",
                            "reference_id": incident_id,
                        },
                        {"_id": 0, "adjustment_id": 1},
                    )
                    if not existing_deduction:
                        deduction_doc = {
                            "adjustment_id": f"adj_{uuid.uuid4().hex[:10]}",
                            "user_id": user_id,
                            "adjustment_type": "late_arrival_deduction",
                            "amount": -deduction_amount,
                            "currency": deduction_currency,
                            "effective_date": local_dt.date().isoformat(),
                            "notes": f"Deducción automática por llegada tarde ({late_after.strftime('%H:%M')}).",
                            "reference_type": "attendance_incident",
                            "reference_id": incident_id,
                            "created_at": now_iso(),
                            "created_by": "system",
                        }
                        await db.hr_payroll_adjustments.insert_one(deduction_doc)
                        await create_user_notification(
                            user_id=user_id,
                            title="Deducción por tardanza aplicada",
                            message=f"Se aplicó una deducción de {deduction_currency} {deduction_amount:.2f} por llegada tarde.",
                            category="payroll",
                        )

        if event_type == "clock_out":
            day_events = await fetch_user_clock_events_for_local_day(user_id, local_dt)
            has_lunch_out = any((item.get("event_type") == "lunch_out") for item in day_events)
            has_lunch_in = any((item.get("event_type") == "lunch_in") for item in day_events)
            if not has_lunch_out:
                await create_attendance_incident(
                    user_id=user_id,
                    user_name=user_name,
                    incident_type="missing_lunch_out",
                    description="Falta marcación de salida a almuerzo.",
                    local_dt=local_dt,
                    source_clock_id=record.get("clock_id"),
                )
            if not has_lunch_in:
                await create_attendance_incident(
                    user_id=user_id,
                    user_name=user_name,
                    incident_type="missing_lunch_in",
                    description="Falta marcación de entrada de almuerzo.",
                    local_dt=local_dt,
                    source_clock_id=record.get("clock_id"),
                )

        if event_type == "lunch_in":
            lunch_break_minutes = max(1, int(settings.get("lunch_break_minutes") or 40))
            day_events = await fetch_user_clock_events_for_local_day(user_id, local_dt)
            lunch_out_events: List[Dict[str, Any]] = [item for item in day_events if item.get("event_type") == "lunch_out"]
            if lunch_out_events:
                latest_lunch_out = lunch_out_events[-1]
                lunch_out_dt = parse_iso(latest_lunch_out.get("created_at"))
                if lunch_out_dt:
                    elapsed_minutes = int((local_dt.astimezone(timezone.utc) - lunch_out_dt).total_seconds() // 60)
                    if elapsed_minutes > lunch_break_minutes:
                        await create_attendance_incident(
                            user_id=user_id,
                            user_name=user_name,
                            incident_type="late_lunch_return",
                            description=f"Entrada de almuerzo tardía ({elapsed_minutes} min). Máximo configurado: {lunch_break_minutes} min.",
                            local_dt=local_dt,
                            source_clock_id=record.get("clock_id"),
                        )
                        await create_user_notification(
                            user_id=user_id,
                            title="Tardanza en entrada de almuerzo",
                            message=f"Se registró retorno de almuerzo con {elapsed_minutes} min (máximo {lunch_break_minutes} min).",
                        )

    def parse_iso(value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return None

    def bi_monthly_next_due(reference: Optional[datetime] = None) -> str:
        base = reference or datetime.now(timezone.utc)
        year = base.year
        month = base.month
        if base.day < 15:
            due = datetime(year, month, 15, tzinfo=timezone.utc)
        else:
            if month == 12:
                due = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
            else:
                due = datetime(year, month + 1, 1, tzinfo=timezone.utc)
        return due.isoformat()

    async def get_user_by_pin(pin: str) -> Dict[str, Any]:
        pin_index = compute_pin_index(pin)
        indexed_user = await db.users.find_one(
            {
                "is_pin_user": True,
                "is_active": True,
                "$or": [
                    {"attendance_pin_index": pin_index},
                    {"pin_index": pin_index},
                ],
            },
            {"_id": 0},
        )
        if indexed_user:
            return indexed_user
        raise HTTPException(status_code=401, detail="PIN inválido")

    async def get_warehouse_names() -> Dict[str, str]:
        docs = await db.warehouses.find({}, {"_id": 0, "warehouse_id": 1, "name": 1}).to_list(300)
        return {
            str(item.get("warehouse_id")): str(item.get("name"))
            for item in docs
            if item.get("warehouse_id") and item.get("name")
        }

    @router.post("/timeclock/punch")
    async def hr_timeclock_punch(payload: Dict[str, Any], request: Request):
        actor = await require_roles(request, HR_ALLOWED_ROLES)
        pin = str((payload or {}).get("pin") or "").strip()
        user_id = str((payload or {}).get("user_id") or "").strip() or None
        event_type = str((payload or {}).get("event_type") or "").strip()
        notes = (payload or {}).get("notes")

        if len(pin) != PIN_LENGTH or not pin.isdigit():
            raise HTTPException(status_code=400, detail="PIN inválido")
        if event_type not in CLOCK_EVENTS:
            raise HTTPException(status_code=400, detail="event_type inválido")

        target_user: Optional[Dict[str, Any]] = None
        if user_id:
            candidate = await db.users.find_one(
                {"user_id": user_id, "is_pin_user": True, "is_active": True},
                {"_id": 0},
            )
            if candidate and verify_pin_hash(pin, get_attendance_pin_hash(candidate)):
                target_user = candidate
        if not target_user:
            target_user = await get_user_by_pin(pin)

        local_now = now_local()
        settings = await get_effective_attendance_settings(target_user.get("branch_id"))
        policy_alerts = validate_clock_window(event_type, local_now, settings)

        anti_double_touch_seconds = int(settings.get("anti_double_touch_seconds") or 20)
        if anti_double_touch_seconds > 0:
            latest_same_event = await db.hr_timeclock_events.find_one(
                {
                    "user_id": target_user.get("user_id"),
                    "event_type": event_type,
                },
                {"_id": 0, "created_at": 1},
                sort=[("created_at", -1)],
            )
            if latest_same_event and latest_same_event.get("created_at"):
                latest_dt = parse_iso(latest_same_event.get("created_at"))
                if latest_dt and (datetime.now(timezone.utc) - latest_dt).total_seconds() < anti_double_touch_seconds:
                    raise HTTPException(status_code=429, detail=f"Marcación duplicada. Intenta en {anti_double_touch_seconds} segundos")

        record = {
            "clock_id": f"clk_{uuid.uuid4().hex[:10]}",
            "user_id": target_user.get("user_id"),
            "user_name": target_user.get("name"),
            "user_role": target_user.get("role"),
            "branch_id": target_user.get("branch_id"),
            "event_type": event_type,
            "notes": notes,
            "created_at": now_iso(),
            "captured_by": actor.user_id,
        }
        await db.hr_timeclock_events.insert_one(record)
        await process_post_clock_rules(record, settings, local_now, policy_alerts=policy_alerts)
        return {"message": "Marcación registrada", "record": {k: v for k, v in record.items() if k != "_id"}}

    @router.post("/timeclock/kiosk-punch")
    async def hr_timeclock_kiosk_punch(payload: Dict[str, Any]):
        pin = str((payload or {}).get("pin") or "").strip()
        user_id = str((payload or {}).get("user_id") or "").strip() or None
        notes = (payload or {}).get("notes")

        if len(pin) != PIN_LENGTH or not pin.isdigit():
            raise HTTPException(status_code=400, detail="PIN inválido")

        target_user: Optional[Dict[str, Any]] = None
        if user_id:
            candidate = await db.users.find_one(
                {"user_id": user_id, "is_pin_user": True, "is_active": True},
                {"_id": 0},
            )
            if candidate and verify_pin_hash(pin, get_attendance_pin_hash(candidate)):
                target_user = candidate
        if not target_user:
            target_user = await get_user_by_pin(pin)

        local_now = now_local()
        settings = await get_effective_attendance_settings(target_user.get("branch_id"))
        today_events_count = await count_user_clock_events_for_local_day(str(target_user.get("user_id")), local_now)
        event_type = expected_clock_event_for_index(today_events_count)

        if not event_type:
            raise HTTPException(status_code=400, detail="Ya completaste tus 4 marcaciones de hoy")

        policy_alerts = validate_clock_window(event_type, local_now, settings)

        anti_double_touch_seconds = int(settings.get("anti_double_touch_seconds") or 20)
        if anti_double_touch_seconds > 0:
            latest_same_event = await db.hr_timeclock_events.find_one(
                {
                    "user_id": target_user.get("user_id"),
                    "event_type": event_type,
                },
                {"_id": 0, "created_at": 1},
                sort=[("created_at", -1)],
            )
            if latest_same_event and latest_same_event.get("created_at"):
                latest_dt = parse_iso(latest_same_event.get("created_at"))
                if latest_dt and (datetime.now(timezone.utc) - latest_dt).total_seconds() < anti_double_touch_seconds:
                    raise HTTPException(status_code=429, detail=f"Marcación duplicada. Intenta en {anti_double_touch_seconds} segundos")

        record = {
            "clock_id": f"clk_{uuid.uuid4().hex[:10]}",
            "user_id": target_user.get("user_id"),
            "user_name": target_user.get("name"),
            "user_role": target_user.get("role"),
            "branch_id": target_user.get("branch_id"),
            "event_type": event_type,
            "notes": notes,
            "created_at": now_iso(),
            "captured_by": "kiosk",
        }
        await db.hr_timeclock_events.insert_one(record)
        await process_post_clock_rules(record, settings, local_now, policy_alerts=policy_alerts)

        next_event = expected_clock_event_for_index(today_events_count + 1)
        return {
            "message": "Marcación registrada",
            "event_type": event_type,
            "event_label": EVENT_LABELS.get(event_type, event_type),
            "next_event_type": next_event,
            "next_event_label": EVENT_LABELS.get(next_event, "Día completado") if next_event else "Día completado",
            "time_format": settings.get("time_format") or "12h",
            "policy_alerts": policy_alerts,
            "record": {k: v for k, v in record.items() if k != "_id"},
        }

    @router.get("/timeclock/events")
    async def hr_timeclock_events(
        request: Request,
        user_id: Optional[str] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
        limit: int = 300,
    ):
        await require_roles(request, HR_ALLOWED_ROLES)
        query: Dict[str, Any] = {}
        if user_id:
            query["user_id"] = user_id
        if start or end:
            query["created_at"] = {}
            if start:
                query["created_at"]["$gte"] = start
            if end:
                query["created_at"]["$lte"] = end

        docs = await db.hr_timeclock_events.find(query, {"_id": 0}).sort("created_at", -1).to_list(limit)
        return docs

    @router.get("/timeclock/pin-directory")
    async def hr_timeclock_pin_directory():
        users = await db.users.find(
            {"is_pin_user": True, "is_active": True},
            {
                "_id": 0,
                "user_id": 1,
                "name": 1,
                "role": 1,
                "branch_id": 1,
                "attendance_pin_index": 1,
                "pin_index": 1,
            },
        ).to_list(3000)
        return [
            {
                **item,
                "pin_index": item.get("attendance_pin_index") or item.get("pin_index"),
            }
            for item in users
            if item.get("attendance_pin_index") or item.get("pin_index")
        ]

    @router.get("/attendance/settings")
    async def get_attendance_settings(request: Request, branch_id: Optional[str] = None):
        await require_roles(request, HR_ALLOWED_ROLES)
        global_doc = await db.hr_attendance_settings.find_one({"scope": "global"}, {"_id": 0})
        branch_doc = None
        if branch_id:
            branch_doc = await db.hr_attendance_settings.find_one({"scope": "branch", "branch_id": branch_id}, {"_id": 0})
        effective = await get_effective_attendance_settings(branch_id)
        return {
            "global": (global_doc or {}).get("settings") or dict(DEFAULT_ATTENDANCE_SETTINGS),
            "branch": (branch_doc or {}).get("settings") if branch_doc else None,
            "effective": effective,
        }

    @router.get("/attendance/settings/public")
    async def get_attendance_settings_public(branch_id: Optional[str] = None):
        effective = await get_effective_attendance_settings(branch_id)
        sync_marker = await get_pin_directory_sync_marker()
        return {
            "time_format": effective.get("time_format") or "12h",
            "kiosk_theme_mode": effective.get("kiosk_theme_mode") or "system",
            "anti_double_touch_seconds": int(effective.get("anti_double_touch_seconds") or 20),
            "lunch_out_start": effective.get("lunch_out_start") or "10:00",
            "lunch_out_end": effective.get("lunch_out_end") or "16:00",
            "lunch_break_minutes": int(effective.get("lunch_break_minutes") or 40),
            "pin_directory_sync_marker": sync_marker,
        }

    @router.post("/timeclock/pin-directory/sync")
    async def sync_timeclock_pin_directory(request: Request):
        actor = await require_roles(request, HR_ALLOWED_ROLES)
        marker = await touch_pin_directory_sync_marker(actor.user_id)
        return {
            "message": "Sincronización de PIN Kiosko solicitada",
            "pin_directory_sync_marker": marker,
        }

    @router.put("/attendance/settings")
    async def update_attendance_settings(payload: Dict[str, Any], request: Request):
        actor = await require_roles(request, HR_ALLOWED_ROLES)
        data = payload or {}
        scope = str(data.get("scope") or "global").strip().lower()
        if scope not in {"global", "branch"}:
            raise HTTPException(status_code=400, detail="scope inválido")

        branch_id = data.get("branch_id") if scope == "branch" else None
        if scope == "branch" and not branch_id:
            raise HTTPException(status_code=400, detail="branch_id es requerido para scope=branch")

        settings_payload = data.get("settings") or {}
        if not isinstance(settings_payload, dict):
            raise HTTPException(status_code=400, detail="settings inválido")

        current_doc = await db.hr_attendance_settings.find_one(
            {"scope": scope, "branch_id": branch_id},
            {"_id": 0, "settings": 1},
        )
        before_settings = (current_doc or {}).get("settings") or dict(DEFAULT_ATTENDANCE_SETTINGS)
        after_settings = dict(before_settings)
        after_settings.update(settings_payload)

        if str(after_settings.get("time_format") or "24h") not in {"12h", "24h"}:
            raise HTTPException(status_code=400, detail="time_format debe ser 12h o 24h")
        if str(after_settings.get("kiosk_theme_mode") or "system") not in {"light", "dark", "system"}:
            raise HTTPException(status_code=400, detail="kiosk_theme_mode debe ser light, dark o system")

        raw_late_deduction_enabled = after_settings.get("late_arrival_deduction_enabled", True)
        if isinstance(raw_late_deduction_enabled, str):
            after_settings["late_arrival_deduction_enabled"] = raw_late_deduction_enabled.strip().lower() in {
                "1",
                "true",
                "yes",
                "si",
                "on",
            }
        else:
            after_settings["late_arrival_deduction_enabled"] = bool(raw_late_deduction_enabled)

        after_settings["late_arrival_deduction_amount"] = max(0.0, float(after_settings.get("late_arrival_deduction_amount") or 0))
        after_settings["late_arrival_deduction_currency"] = (
            str(after_settings.get("late_arrival_deduction_currency") or "NIO").strip().upper() or "NIO"
        )

        after_settings["entry_tolerance_minutes"] = max(0, int(after_settings.get("entry_tolerance_minutes") or 10))
        after_settings["anti_double_touch_seconds"] = max(0, int(after_settings.get("anti_double_touch_seconds") or 20))
        after_settings["lunch_break_minutes"] = max(1, int(after_settings.get("lunch_break_minutes") or 40))

        await db.hr_attendance_settings.update_one(
            {"scope": scope, "branch_id": branch_id},
            {
                "$set": {
                    "scope": scope,
                    "branch_id": branch_id,
                    "settings": after_settings,
                    "updated_by": actor.user_id,
                    "updated_at": now_iso(),
                }
            },
            upsert=True,
        )

        await write_attendance_settings_audit(
            actor_user_id=actor.user_id,
            scope=scope,
            branch_id=branch_id,
            before_settings=before_settings,
            after_settings=after_settings,
        )

        return {"message": "Configuración de asistencia actualizada", "scope": scope, "branch_id": branch_id, "settings": after_settings}

    @router.get("/attendance/settings/audit")
    async def get_attendance_settings_audit(request: Request, limit: int = 100):
        await require_roles(request, HR_ALLOWED_ROLES)
        return await db.hr_attendance_settings_audit.find({}, {"_id": 0}).sort("changed_at", -1).to_list(limit)

    @router.get("/attendance/incidents")
    async def get_attendance_incidents(request: Request, limit: int = 200):
        await require_roles(request, HR_ALLOWED_ROLES)
        return await db.hr_attendance_incidents.find({}, {"_id": 0}).sort("created_at", -1).to_list(limit)

    @router.get("/attendance/reports/biweekly")
    async def get_attendance_biweekly_report(
        request: Request,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        branch_id: Optional[str] = None,
        include_test_users: bool = False,
    ):
        await require_roles(request, HR_ALLOWED_ROLES)

        def is_test_user(user_doc: Dict[str, Any]) -> bool:
            name = str(user_doc.get("name") or "").strip().lower()
            email = str(user_doc.get("email") or "").strip().lower()
            user_id = str(user_doc.get("user_id") or "").strip().lower()
            test_tokens = ["e2e", "test", "debug", "playwright"]
            return any(token in name for token in test_tokens) or any(token in email for token in test_tokens) or any(
                token in user_id for token in test_tokens
            )

        def build_events_by_day(events: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
            events_by_day: Dict[str, List[Dict[str, Any]]] = {}
            for item in events:
                created_at = parse_iso(item.get("created_at"))
                if not created_at:
                    continue
                local_dt = created_at.astimezone(ATTENDANCE_TIMEZONE)
                day_key = local_dt.date().isoformat()
                events_by_day.setdefault(day_key, []).append(item)
            return events_by_day

        def classify_compliance(absences: int, late_minutes: int, lunch_over_minutes: int) -> str:
            if absences >= 2 or late_minutes > 60 or lunch_over_minutes > 60:
                return "rojo"
            if absences >= 1 or late_minutes > 15 or lunch_over_minutes > 20:
                return "amarillo"
            return "verde"

        def build_metrics_for_range(
            user_settings: Dict[str, Any],
            events_by_day: Dict[str, List[Dict[str, Any]]],
            date_start: datetime.date,
            date_end: datetime.date,
        ) -> Dict[str, Any]:
            range_days_local = (date_end - date_start).days + 1
            tardies = 0
            absences = 0
            overtime_minutes = 0
            late_minutes = 0
            lunch_over_minutes = 0
            worked_minutes_total = 0
            worked_minutes_by_week: Dict[str, int] = {}
            daily_details: List[Dict[str, Any]] = []

            for day_offset in range(range_days_local):
                current_date = date_start + timedelta(days=day_offset)
                if current_date.weekday() == 6:
                    continue

                day_key = current_date.isoformat()
                day_events = events_by_day.get(day_key, [])

                first_clock_in = None
                first_lunch_out = None
                first_lunch_in = None
                last_clock_out = None

                for event in day_events:
                    e_type = event.get("event_type")
                    e_dt = parse_iso(event.get("created_at"))
                    if not e_dt:
                        continue
                    e_local = e_dt.astimezone(ATTENDANCE_TIMEZONE)

                    if e_type == "clock_in" and first_clock_in is None:
                        first_clock_in = e_local
                    if e_type == "lunch_out" and first_lunch_out is None:
                        first_lunch_out = e_local
                    if (
                        e_type == "lunch_in"
                        and first_lunch_in is None
                        and (first_lunch_out is None or e_local >= first_lunch_out)
                    ):
                        first_lunch_in = e_local
                    if e_type == "clock_out":
                        last_clock_out = e_local

                if not first_clock_in:
                    absences += 1
                    daily_details.append(
                        {
                            "date": day_key,
                            "clock_in": None,
                            "lunch_out": None,
                            "lunch_in": None,
                            "clock_out": None,
                            "worked_hours": 0.0,
                            "late_minutes": 0,
                            "lunch_over_minutes": 0,
                            "status": "ausente",
                        }
                    )
                    continue

                entry_start = parse_hhmm(str(user_settings.get("entry_start") or "08:00"), "08:00")
                tolerance_minutes = int(user_settings.get("entry_tolerance_minutes") or 10)
                late_after = datetime.combine(current_date, entry_start, tzinfo=ATTENDANCE_TIMEZONE) + timedelta(
                    minutes=max(0, tolerance_minutes)
                )

                day_late_minutes = 0
                if first_clock_in > late_after:
                    tardies += 1
                    day_late_minutes = int((first_clock_in - late_after).total_seconds() // 60)
                    late_minutes += day_late_minutes

                lunch_window_minutes = 0
                day_lunch_over_minutes = 0
                if first_lunch_out and first_lunch_in and first_lunch_in > first_lunch_out:
                    lunch_window_minutes = int((first_lunch_in - first_lunch_out).total_seconds() // 60)
                    allowed_lunch_minutes = int(user_settings.get("lunch_break_minutes") or 40)
                    if lunch_window_minutes > allowed_lunch_minutes:
                        day_lunch_over_minutes = lunch_window_minutes - allowed_lunch_minutes
                        lunch_over_minutes += day_lunch_over_minutes

                worked_minutes_day = 0
                if last_clock_out and last_clock_out > first_clock_in:
                    worked_minutes_day = int((last_clock_out - first_clock_in).total_seconds() // 60)
                    worked_minutes_day = max(0, worked_minutes_day - max(0, lunch_window_minutes))
                    worked_minutes_total += worked_minutes_day
                    iso_week = current_date.isocalendar()
                    week_key = f"{iso_week.year}-W{iso_week.week:02d}"
                    worked_minutes_by_week[week_key] = worked_minutes_by_week.get(week_key, 0) + worked_minutes_day

                if last_clock_out:
                    shift_end = get_shift_end_time(last_clock_out, user_settings)
                    shift_end_dt = datetime.combine(current_date, shift_end, tzinfo=ATTENDANCE_TIMEZONE)
                    if last_clock_out > shift_end_dt:
                        overtime_minutes += int((last_clock_out - shift_end_dt).total_seconds() // 60)

                daily_details.append(
                    {
                        "date": day_key,
                        "clock_in": first_clock_in.isoformat() if first_clock_in else None,
                        "lunch_out": first_lunch_out.isoformat() if first_lunch_out else None,
                        "lunch_in": first_lunch_in.isoformat() if first_lunch_in else None,
                        "clock_out": last_clock_out.isoformat() if last_clock_out else None,
                        "worked_hours": round(worked_minutes_day / 60, 2),
                        "late_minutes": day_late_minutes,
                        "lunch_over_minutes": day_lunch_over_minutes,
                        "status": "ok",
                    }
                )

            worked_hours_by_week = {
                key: round(minutes / 60, 2)
                for key, minutes in sorted(worked_minutes_by_week.items())
            }
            week_keys = list(worked_hours_by_week.keys())
            week_1_hours = worked_hours_by_week.get(week_keys[0], 0.0) if len(week_keys) >= 1 else 0.0
            week_2_hours = worked_hours_by_week.get(week_keys[1], 0.0) if len(week_keys) >= 2 else 0.0

            return {
                "tardies": tardies,
                "late_minutes": late_minutes,
                "absences": absences,
                "lunch_over_minutes": lunch_over_minutes,
                "worked_minutes_by_week": worked_minutes_by_week,
                "worked_hours_by_week": worked_hours_by_week,
                "worked_hours_weekly_text": " | ".join(
                    [f"{key}: {value:.2f}h" for key, value in worked_hours_by_week.items()]
                ),
                "worked_hours_week_1": week_1_hours,
                "worked_hours_week_2": week_2_hours,
                "worked_minutes_biweekly": worked_minutes_total,
                "worked_hours_biweekly": round(worked_minutes_total / 60, 2),
                "estimated_overtime_minutes": overtime_minutes,
                "daily_details": daily_details,
            }

        now_local_dt = now_local()
        if start_date and end_date:
            try:
                start_local_date = datetime.fromisoformat(start_date).date()
                end_local_date = datetime.fromisoformat(end_date).date()
            except ValueError:
                raise HTTPException(status_code=400, detail="Fechas inválidas")
        else:
            if now_local_dt.day <= 15:
                start_local_date = now_local_dt.date().replace(day=1)
                end_local_date = now_local_dt.date().replace(day=15)
            else:
                start_local_date = now_local_dt.date().replace(day=16)
                end_local_date = now_local_dt.date()

        start_local = datetime.combine(start_local_date, time(0, 0), tzinfo=ATTENDANCE_TIMEZONE)
        end_local = datetime.combine(end_local_date + timedelta(days=1), time(0, 0), tzinfo=ATTENDANCE_TIMEZONE)
        start_utc_iso = start_local.astimezone(timezone.utc).isoformat()
        end_utc_iso = end_local.astimezone(timezone.utc).isoformat()

        range_days = (end_local_date - start_local_date).days + 1
        previous_end_date = start_local_date - timedelta(days=1)
        previous_start_date = previous_end_date - timedelta(days=range_days - 1)
        previous_start_local = datetime.combine(previous_start_date, time(0, 0), tzinfo=ATTENDANCE_TIMEZONE)
        previous_end_local = datetime.combine(previous_end_date + timedelta(days=1), time(0, 0), tzinfo=ATTENDANCE_TIMEZONE)
        previous_start_utc_iso = previous_start_local.astimezone(timezone.utc).isoformat()
        previous_end_utc_iso = previous_end_local.astimezone(timezone.utc).isoformat()

        user_query: Dict[str, Any] = {"is_pin_user": True, "is_active": True}
        if branch_id:
            user_query["branch_id"] = branch_id
        users = await db.users.find(
            user_query,
            {"_id": 0, "user_id": 1, "name": 1, "email": 1, "role": 1, "branch_id": 1},
        ).to_list(3000)

        report_rows: List[Dict[str, Any]] = []

        for user in users:
            if not include_test_users and is_test_user(user):
                continue

            user_id = user.get("user_id")
            settings = await get_effective_attendance_settings(user.get("branch_id"))

            current_events = await db.hr_timeclock_events.find(
                {
                    "user_id": user_id,
                    "created_at": {"$gte": start_utc_iso, "$lt": end_utc_iso},
                },
                {"_id": 0},
            ).sort("created_at", 1).to_list(5000)

            previous_events = await db.hr_timeclock_events.find(
                {
                    "user_id": user_id,
                    "created_at": {"$gte": previous_start_utc_iso, "$lt": previous_end_utc_iso},
                },
                {"_id": 0},
            ).sort("created_at", 1).to_list(5000)

            current_metrics = build_metrics_for_range(
                user_settings=settings,
                events_by_day=build_events_by_day(current_events),
                date_start=start_local_date,
                date_end=end_local_date,
            )
            previous_metrics = build_metrics_for_range(
                user_settings=settings,
                events_by_day=build_events_by_day(previous_events),
                date_start=previous_start_date,
                date_end=previous_end_date,
            )

            compliance_status = classify_compliance(
                absences=int(current_metrics.get("absences") or 0),
                late_minutes=int(current_metrics.get("late_minutes") or 0),
                lunch_over_minutes=int(current_metrics.get("lunch_over_minutes") or 0),
            )

            report_rows.append(
                {
                    "user_id": user_id,
                    "user_name": user.get("name"),
                    "role": user.get("role"),
                    "branch_id": user.get("branch_id"),
                    **current_metrics,
                    "compliance_status": compliance_status,
                    "compare_worked_hours_biweekly": previous_metrics.get("worked_hours_biweekly") or 0,
                    "compare_late_minutes": previous_metrics.get("late_minutes") or 0,
                    "compare_lunch_over_minutes": previous_metrics.get("lunch_over_minutes") or 0,
                    "compare_worked_hours_biweekly_delta": round(
                        float(current_metrics.get("worked_hours_biweekly") or 0)
                        - float(previous_metrics.get("worked_hours_biweekly") or 0),
                        2,
                    ),
                    "compare_late_minutes_delta": int(current_metrics.get("late_minutes") or 0)
                    - int(previous_metrics.get("late_minutes") or 0),
                    "compare_lunch_over_minutes_delta": int(current_metrics.get("lunch_over_minutes") or 0)
                    - int(previous_metrics.get("lunch_over_minutes") or 0),
                }
            )

        total_worked_hours = round(sum(float(item.get("worked_hours_biweekly") or 0) for item in report_rows), 2)
        total_late_minutes = int(sum(int(item.get("late_minutes") or 0) for item in report_rows))
        total_lunch_over_minutes = int(sum(int(item.get("lunch_over_minutes") or 0) for item in report_rows))
        total_absences = int(sum(int(item.get("absences") or 0) for item in report_rows))
        compliance_counts = {
            "verde": len([item for item in report_rows if item.get("compliance_status") == "verde"]),
            "amarillo": len([item for item in report_rows if item.get("compliance_status") == "amarillo"]),
            "rojo": len([item for item in report_rows if item.get("compliance_status") == "rojo"]),
        }

        top_incidents = sorted(
            report_rows,
            key=lambda item: (
                int(item.get("late_minutes") or 0)
                + int(item.get("lunch_over_minutes") or 0)
                + (int(item.get("absences") or 0) * 30)
            ),
            reverse=True,
        )[:5]

        auto_alerts = [
            {
                "user_id": item.get("user_id"),
                "user_name": item.get("user_name"),
                "severity": item.get("compliance_status"),
                "message": f"{item.get('user_name')}: tardanza {item.get('late_minutes', 0)} min, almuerzo excedido {item.get('lunch_over_minutes', 0)} min, ausencias {item.get('absences', 0)}",
            }
            for item in report_rows
            if item.get("compliance_status") in {"amarillo", "rojo"}
        ]

        return {
            "start_date": start_local_date.isoformat(),
            "end_date": end_local_date.isoformat(),
            "previous_start_date": previous_start_date.isoformat(),
            "previous_end_date": previous_end_date.isoformat(),
            "summary": {
                "total_worked_hours": total_worked_hours,
                "total_late_minutes": total_late_minutes,
                "total_lunch_over_minutes": total_lunch_over_minutes,
                "total_absences": total_absences,
                "compliance_counts": compliance_counts,
                "top_incidents": [
                    {
                        "user_id": item.get("user_id"),
                        "user_name": item.get("user_name"),
                        "late_minutes": item.get("late_minutes"),
                        "lunch_over_minutes": item.get("lunch_over_minutes"),
                        "absences": item.get("absences"),
                        "compliance_status": item.get("compliance_status"),
                    }
                    for item in top_incidents
                ],
                "alerts": auto_alerts,
            },
            "rows": report_rows,
        }

    @router.get("/attendance/reports/biweekly/export")
    async def export_attendance_biweekly_report(
        request: Request,
        format: str = "csv",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        branch_id: Optional[str] = None,
        include_test_users: bool = False,
    ):
        fmt = (format or "csv").strip().lower()
        if fmt not in {"csv", "excel", "pdf"}:
            raise HTTPException(status_code=400, detail="Formato no soportado")

        report = await get_attendance_biweekly_report(
            request=request,
            start_date=start_date,
            end_date=end_date,
            branch_id=branch_id,
            include_test_users=include_test_users,
        )
        rows = report.get("rows") or []

        export_rows = [
            {
                "ID Usuario": item.get("user_id") or "",
                "Usuario": item.get("user_name") or "",
                "Rol": item.get("role") or "",
                "Sucursal": item.get("branch_id") or "",
                "Semáforo": item.get("compliance_status") or "",
                "Horas Semana": item.get("worked_hours_weekly_text") or "",
                "Semana 1 (h)": item.get("worked_hours_week_1") or 0,
                "Semana 2 (h)": item.get("worked_hours_week_2") or 0,
                "Horas Quincena": item.get("worked_hours_biweekly") or 0,
                "Tardanzas": item.get("tardies") or 0,
                "Min Tardanza": item.get("late_minutes") or 0,
                "Ausencias": item.get("absences") or 0,
                "Min Exceso Almuerzo": item.get("lunch_over_minutes") or 0,
                "Horas Extra (min)": item.get("estimated_overtime_minutes") or 0,
                "Δ Horas Quincena": item.get("compare_worked_hours_biweekly_delta") or 0,
                "Δ Min Tardanza": item.get("compare_late_minutes_delta") or 0,
                "Δ Min Almuerzo": item.get("compare_lunch_over_minutes_delta") or 0,
            }
            for item in rows
        ]

        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        start_label = report.get("start_date") or "inicio"
        end_label = report.get("end_date") or "fin"

        if fmt == "excel":
            df = pd.DataFrame(export_rows)
            payroll_df = pd.DataFrame(
                [
                    {
                        "ID Usuario": item.get("ID Usuario"),
                        "Usuario": item.get("Usuario"),
                        "Horas Quincena": item.get("Horas Quincena"),
                        "Min Tardanza": item.get("Min Tardanza"),
                        "Min Exceso Almuerzo": item.get("Min Exceso Almuerzo"),
                        "Ausencias": item.get("Ausencias"),
                        "Horas Extra (min)": item.get("Horas Extra (min)"),
                        "Semáforo": item.get("Semáforo"),
                    }
                    for item in export_rows
                ]
            )
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="ReporteQuincenal")
                payroll_df.to_excel(writer, index=False, sheet_name="NominaReady")
            excel_buffer.seek(0)
            return StreamingResponse(
                excel_buffer,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={
                    "Content-Disposition": f"attachment; filename=attendance_biweekly_{start_label}_{end_label}_{ts}.xlsx",
                },
            )

        if fmt == "pdf":
            pdf_buffer = io.BytesIO()
            pdf = canvas.Canvas(pdf_buffer, pagesize=letter)
            width, height = letter
            y = height - 36

            pdf.setFont("Helvetica-Bold", 12)
            pdf.drawString(30, y, "Reporte quincenal de asistencia")
            y -= 16
            pdf.setFont("Helvetica", 9)
            pdf.drawString(30, y, f"Rango: {start_label} a {end_label}")
            y -= 18

            pdf.setFont("Helvetica-Bold", 8)
            pdf.drawString(30, y, "Usuario")
            pdf.drawString(195, y, "Hrs Qna")
            pdf.drawString(255, y, "Min Tard")
            pdf.drawString(325, y, "Min Alm")
            pdf.drawString(395, y, "Aus")
            pdf.drawString(435, y, "Extra")
            y -= 10
            pdf.line(30, y, width - 30, y)
            y -= 12

            pdf.setFont("Helvetica", 8)
            for row in export_rows:
                if y < 36:
                    pdf.showPage()
                    y = height - 36
                    pdf.setFont("Helvetica", 8)
                pdf.drawString(30, y, str(row.get("Usuario") or "")[:28])
                pdf.drawRightString(245, y, str(row.get("Horas Quincena") or 0))
                pdf.drawRightString(315, y, str(row.get("Min Tardanza") or 0))
                pdf.drawRightString(385, y, str(row.get("Min Exceso Almuerzo") or 0))
                pdf.drawRightString(425, y, str(row.get("Ausencias") or 0))
                pdf.drawRightString(515, y, str(row.get("Horas Extra (min)") or 0))
                y -= 11

            pdf.save()
            pdf_buffer.seek(0)
            return StreamingResponse(
                pdf_buffer,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename=attendance_biweekly_{start_label}_{end_label}_{ts}.pdf",
                },
            )

        output = io.StringIO()
        fieldnames = [
            "ID Usuario",
            "Usuario",
            "Rol",
            "Sucursal",
            "Horas Semana",
            "Horas Quincena",
            "Tardanzas",
            "Min Tardanza",
            "Ausencias",
            "Min Exceso Almuerzo",
            "Horas Extra (min)",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(export_rows)

        csv_content = output.getvalue()
        output.close()
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=attendance_biweekly_{report.get('start_date')}_{report.get('end_date')}.csv",
            },
        )

    @router.get("/my/overview")
    async def get_my_hr_overview(request: Request, limit: int = 120):
        current_user = await require_auth(request)
        user_id = current_user.user_id

        incidents = await db.hr_attendance_incidents.find(
            {"user_id": user_id},
            {"_id": 0},
        ).sort("created_at", -1).to_list(limit)

        sanctions = await db.hr_personnel_actions.find(
            {"user_id": user_id, "action_type": "sancion"},
            {"_id": 0},
        ).sort("created_at", -1).to_list(limit)

        notifications = await db.hr_notifications.find(
            {"user_id": user_id},
            {"_id": 0},
        ).sort("created_at", -1).to_list(limit)

        payroll_adjustments = await db.hr_payroll_adjustments.find(
            {"user_id": user_id},
            {"_id": 0},
        ).sort("created_at", -1).to_list(limit)

        current_year = datetime.now(ATTENDANCE_TIMEZONE).year
        year_start = f"{current_year}-01-01"
        year_end = f"{current_year}-12-31"
        approved_vacations = await db.hr_leaves.find(
            {
                "user_id": user_id,
                "leave_type": "vacaciones",
                "status": {"$in": ["approved", "aprobado", "activo"]},
                "start_date": {"$lte": year_end},
                "end_date": {"$gte": year_start},
            },
            {"_id": 0},
        ).to_list(500)

        vacation_days_used = 0
        for leave in approved_vacations:
            try:
                start_dt = datetime.fromisoformat(str(leave.get("start_date"))[:10]).date()
                end_dt = datetime.fromisoformat(str(leave.get("end_date"))[:10]).date()
                vacation_days_used += max(0, (end_dt - start_dt).days + 1)
            except Exception:
                continue

        vacation_allowance_days = int(os.environ.get("HR_VACATION_ALLOWANCE_DAYS", "15"))
        vacation_days_available = max(0, vacation_allowance_days - vacation_days_used)

        sales_docs = await db.sales.find(
            {
                "$or": [
                    {"salesperson_id": user_id},
                    {"seller_id": user_id},
                    {"created_by": user_id},
                ]
            },
            {"_id": 0, "sale_id": 1, "total": 1, "created_at": 1, "status": 1},
        ).sort("created_at", -1).to_list(limit)

        total_sales_amount = round(sum(float(item.get("total") or 0) for item in sales_docs), 2)
        commission_rate = float(os.environ.get("HR_DEFAULT_COMMISSION_RATE", "0.03"))
        estimated_commission = round(total_sales_amount * commission_rate, 2)

        return {
            "user_id": user_id,
            "user_name": current_user.name,
            "incidents": incidents,
            "sanctions": sanctions,
            "notifications": notifications,
            "payroll_adjustments": payroll_adjustments,
            "vacations": {
                "allowance_days": vacation_allowance_days,
                "used_days": vacation_days_used,
                "available_days": vacation_days_available,
                "records": approved_vacations,
            },
            "sales_commissions": {
                "commission_rate": commission_rate,
                "total_sales": total_sales_amount,
                "estimated_commission": estimated_commission,
                "sales_count": len(sales_docs),
                "recent_sales": sales_docs,
            },
        }

    @router.post("/leaves")
    async def create_leave(payload: Dict[str, Any], request: Request):
        actor = await require_roles(request, HR_ALLOWED_ROLES)
        data = payload or {}
        leave_type = str(data.get("leave_type") or "").strip().lower()
        if leave_type not in {"vacaciones", "permiso", "subsidio"}:
            raise HTTPException(status_code=400, detail="leave_type inválido")
        user_id = data.get("user_id")
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        if not user_id or not start_date or not end_date:
            raise HTTPException(status_code=400, detail="user_id, start_date y end_date son requeridos")

        doc = {
            "leave_id": f"lv_{uuid.uuid4().hex[:10]}",
            "user_id": user_id,
            "leave_type": leave_type,
            "start_date": start_date,
            "end_date": end_date,
            "paid": bool(data.get("paid", leave_type != "permiso")),
            "notes": data.get("notes"),
            "status": str(data.get("status") or "approved"),
            "created_at": now_iso(),
            "created_by": actor.user_id,
        }
        await db.hr_leaves.insert_one(doc)
        return {"message": "Novedad de ausencia registrada", "leave_id": doc["leave_id"]}

    @router.get("/leaves")
    async def get_leaves(request: Request, user_id: Optional[str] = None, limit: int = 300):
        await require_roles(request, HR_ALLOWED_ROLES)
        query: Dict[str, Any] = {}
        if user_id:
            query["user_id"] = user_id
        return await db.hr_leaves.find(query, {"_id": 0}).sort("created_at", -1).to_list(limit)

    @router.post("/payroll-adjustments")
    async def create_payroll_adjustment(payload: Dict[str, Any], request: Request):
        actor = await require_roles(request, HR_ALLOWED_ROLES)
        data = payload or {}
        user_id = data.get("user_id")
        adjustment_type = str(data.get("adjustment_type") or "").strip().lower()
        amount = float(data.get("amount") or 0)

        if not user_id or not adjustment_type or amount == 0:
            raise HTTPException(status_code=400, detail="user_id, adjustment_type y amount son requeridos")

        negative_types = {
            "penalizacion",
            "multa",
            "sancion",
            "descuento_herramienta",
            "tool_missing_deduction",
            "late_arrival_deduction",
        }
        if adjustment_type in negative_types and amount > 0:
            amount = -amount

        doc = {
            "adjustment_id": f"adj_{uuid.uuid4().hex[:10]}",
            "user_id": user_id,
            "adjustment_type": adjustment_type,
            "amount": amount,
            "currency": str(data.get("currency") or "NIO"),
            "effective_date": data.get("effective_date") or now_iso(),
            "notes": data.get("notes"),
            "reference_type": data.get("reference_type"),
            "reference_id": data.get("reference_id"),
            "created_at": now_iso(),
            "created_by": actor.user_id,
        }
        await db.hr_payroll_adjustments.insert_one(doc)
        return {"message": "Ajuste de nómina registrado", "adjustment_id": doc["adjustment_id"]}

    @router.get("/payroll-adjustments")
    async def get_payroll_adjustments(
        request: Request,
        user_id: Optional[str] = None,
        adjustment_type: Optional[str] = None,
        limit: int = 400,
    ):
        await require_roles(request, HR_ALLOWED_ROLES)
        query: Dict[str, Any] = {}
        if user_id:
            query["user_id"] = user_id
        if adjustment_type:
            query["adjustment_type"] = adjustment_type
        return await db.hr_payroll_adjustments.find(query, {"_id": 0}).sort("created_at", -1).to_list(limit)

    @router.post("/personnel-actions")
    async def create_personnel_action(payload: Dict[str, Any], request: Request):
        actor = await require_roles(request, HR_ALLOWED_ROLES)
        data = payload or {}
        action_type = str(data.get("action_type") or "").strip().lower()
        if action_type not in {"contratacion", "despido", "ascenso", "sancion"}:
            raise HTTPException(status_code=400, detail="action_type inválido")

        doc = {
            "action_id": f"act_{uuid.uuid4().hex[:10]}",
            "action_type": action_type,
            "user_id": data.get("user_id"),
            "employee_name": data.get("employee_name"),
            "old_role": data.get("old_role"),
            "new_role": data.get("new_role"),
            "effective_date": data.get("effective_date") or now_iso(),
            "notes": data.get("notes"),
            "created_at": now_iso(),
            "created_by": actor.user_id,
        }
        await db.hr_personnel_actions.insert_one(doc)
        return {"message": "Movimiento de personal registrado", "action_id": doc["action_id"]}

    @router.get("/personnel-actions")
    async def get_personnel_actions(request: Request, limit: int = 300):
        await require_roles(request, HR_ALLOWED_ROLES)
        return await db.hr_personnel_actions.find({}, {"_id": 0}).sort("created_at", -1).to_list(limit)

    @router.post("/operational-expenses")
    async def create_operational_expense(payload: Dict[str, Any], request: Request):
        actor = await require_roles(request, HR_ALLOWED_ROLES)
        data = payload or {}
        amount = float(data.get("amount") or 0)
        if amount <= 0:
            raise HTTPException(status_code=400, detail="amount debe ser mayor a 0")

        doc = {
            "expense_id": f"ope_{uuid.uuid4().hex[:10]}",
            "category": str(data.get("category") or "operativo"),
            "description": data.get("description"),
            "amount": amount,
            "currency": str(data.get("currency") or "NIO"),
            "expense_date": data.get("expense_date") or now_iso(),
            "branch_id": data.get("branch_id"),
            "created_at": now_iso(),
            "created_by": actor.user_id,
        }
        await db.hr_operational_expenses.insert_one(doc)
        return {"message": "Gasto operativo registrado", "expense_id": doc["expense_id"]}

    @router.get("/operational-expenses")
    async def get_operational_expenses(request: Request, limit: int = 300):
        await require_roles(request, HR_ALLOWED_ROLES)
        return await db.hr_operational_expenses.find({}, {"_id": 0}).sort("created_at", -1).to_list(limit)

    @router.post("/purchase-orders")
    async def create_purchase_order(payload: Dict[str, Any], request: Request):
        actor = await require_roles(request, HR_ALLOWED_ROLES)
        data = payload or {}
        supplier = data.get("supplier")
        items = data.get("items")
        if not supplier or not isinstance(items, list) or len(items) == 0:
            raise HTTPException(status_code=400, detail="supplier e items son requeridos")

        total_amount = 0.0
        normalized_items: List[Dict[str, Any]] = []
        for item in items:
            quantity = float((item or {}).get("quantity") or 0)
            unit_cost = float((item or {}).get("unit_cost") or 0)
            if quantity <= 0:
                continue
            line_total = quantity * unit_cost
            total_amount += line_total
            normalized_items.append(
                {
                    "item_name": (item or {}).get("item_name"),
                    "quantity": quantity,
                    "unit_cost": unit_cost,
                    "line_total": line_total,
                }
            )
        if len(normalized_items) == 0:
            raise HTTPException(status_code=400, detail="items inválidos")

        doc = {
            "po_id": f"po_{uuid.uuid4().hex[:10]}",
            "supplier": supplier,
            "items": normalized_items,
            "status": str(data.get("status") or "pending"),
            "total_amount": total_amount,
            "currency": str(data.get("currency") or "NIO"),
            "requested_by": actor.user_id,
            "approved_by": data.get("approved_by"),
            "created_at": now_iso(),
            "notes": data.get("notes"),
        }
        await db.hr_purchase_orders.insert_one(doc)
        return {"message": "Orden de compra registrada", "po_id": doc["po_id"]}

    @router.get("/purchase-orders")
    async def get_purchase_orders(request: Request, status: Optional[str] = None, limit: int = 300):
        await require_roles(request, HR_ALLOWED_ROLES)
        query: Dict[str, Any] = {}
        if status:
            query["status"] = status
        return await db.hr_purchase_orders.find(query, {"_id": 0}).sort("created_at", -1).to_list(limit)

    @router.post("/tools/assignments")
    async def assign_tool(payload: Dict[str, Any], request: Request):
        actor = await require_roles(request, HR_ALLOWED_ROLES)
        data = payload or {}
        technician_id = data.get("technician_id")
        if not technician_id:
            raise HTTPException(status_code=400, detail="technician_id es requerido")
        category = str(data.get("category") or "instalador").strip().lower()
        if category not in {"instalador", "electrico", "polarizador"}:
            raise HTTPException(status_code=400, detail="category inválida")

        doc = {
            "assignment_id": f"tool_{uuid.uuid4().hex[:10]}",
            "technician_id": technician_id,
            "technician_name": data.get("technician_name"),
            "category": category,
            "tool_name": data.get("tool_name"),
            "serial": data.get("serial"),
            "unit_cost": float(data.get("unit_cost") or 0),
            "status": str(data.get("status") or "assigned"),
            "assigned_at": now_iso(),
            "assigned_by": actor.user_id,
        }
        await db.hr_tool_assignments.insert_one(doc)
        return {"message": "Herramienta asignada", "assignment_id": doc["assignment_id"]}

    @router.get("/tools/assignments")
    async def get_tool_assignments(
        request: Request,
        technician_id: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 1000,
    ):
        await require_roles(request, HR_ALLOWED_ROLES)
        query: Dict[str, Any] = {}
        if technician_id:
            query["technician_id"] = technician_id
        if category:
            query["category"] = category
        return await db.hr_tool_assignments.find(query, {"_id": 0}).sort("assigned_at", -1).to_list(limit)

    @router.post("/tools/audits")
    async def create_tool_audit(payload: Dict[str, Any], request: Request):
        actor = await require_roles(request, HR_ALLOWED_ROLES)
        data = payload or {}
        technician_id = data.get("technician_id")
        if not technician_id:
            raise HTTPException(status_code=400, detail="technician_id es requerido")

        assigned = await db.hr_tool_assignments.find(
            {"technician_id": technician_id, "status": {"$ne": "removed"}},
            {"_id": 0},
        ).to_list(500)
        expected_serials = {
            str(item.get("serial"))
            for item in assigned
            if item.get("serial")
        }
        found_serials = {
            str(item).strip()
            for item in (data.get("found_serials") or [])
            if str(item).strip()
        }

        missing_serials = sorted(list(expected_serials - found_serials))
        missing_items = [
            {
                "assignment_id": item.get("assignment_id"),
                "tool_name": item.get("tool_name"),
                "serial": item.get("serial"),
                "unit_cost": float(item.get("unit_cost") or 0),
            }
            for item in assigned
            if item.get("serial") in missing_serials
        ]
        missing_cost_total = sum(float(item.get("unit_cost") or 0) for item in missing_items)

        audit_doc = {
            "audit_id": f"aud_{uuid.uuid4().hex[:10]}",
            "technician_id": technician_id,
            "technician_name": data.get("technician_name"),
            "category": data.get("category"),
            "expected_count": len(expected_serials),
            "found_count": len(found_serials),
            "missing_count": len(missing_items),
            "missing_items": missing_items,
            "missing_cost_total": missing_cost_total,
            "status": "pending_deduction" if missing_items else "closed_ok",
            "created_at": now_iso(),
            "created_by": actor.user_id,
            "next_due_at": bi_monthly_next_due(),
        }
        await db.hr_tool_audits.insert_one(audit_doc)

        return {
            "message": "Auditoría de herramientas registrada",
            "audit_id": audit_doc["audit_id"],
            "missing_count": audit_doc["missing_count"],
            "missing_cost_total": audit_doc["missing_cost_total"],
        }

    @router.put("/tools/audits/{audit_id}/apply-deductions")
    async def apply_tool_deductions(audit_id: str, request: Request):
        actor = await require_roles(request, HR_ALLOWED_ROLES)
        audit = await db.hr_tool_audits.find_one({"audit_id": audit_id}, {"_id": 0})
        if not audit:
            raise HTTPException(status_code=404, detail="Auditoría no encontrada")
        if audit.get("deductions_applied_at"):
            return {"message": "Descuentos ya aplicados", "audit_id": audit_id}

        missing_items = audit.get("missing_items") or []
        created_adjustments = []
        for item in missing_items:
            amount = float(item.get("unit_cost") or 0)
            if amount <= 0:
                continue
            adjustment = {
                "adjustment_id": f"adj_{uuid.uuid4().hex[:10]}",
                "user_id": audit.get("technician_id"),
                "adjustment_type": "tool_missing_deduction",
                "amount": -abs(amount),
                "currency": "NIO",
                "effective_date": now_iso(),
                "notes": f"Descuento por herramienta faltante: {item.get('tool_name')} ({item.get('serial')})",
                "reference_type": "tool_audit",
                "reference_id": audit_id,
                "created_at": now_iso(),
                "created_by": actor.user_id,
            }
            await db.hr_payroll_adjustments.insert_one(adjustment)
            created_adjustments.append(adjustment["adjustment_id"])

        await db.hr_tool_audits.update_one(
            {"audit_id": audit_id},
            {
                "$set": {
                    "deductions_applied_at": now_iso(),
                    "deductions_applied_by": actor.user_id,
                    "status": "closed_with_deduction" if missing_items else "closed_ok",
                }
            },
        )

        return {
            "message": "Descuentos aplicados",
            "audit_id": audit_id,
            "adjustments_created": created_adjustments,
        }

    @router.get("/tools/audits")
    async def get_tool_audits(request: Request, technician_id: Optional[str] = None, limit: int = 300):
        await require_roles(request, HR_ALLOWED_ROLES)
        query: Dict[str, Any] = {}
        if technician_id:
            query["technician_id"] = technician_id
        return await db.hr_tool_audits.find(query, {"_id": 0}).sort("created_at", -1).to_list(limit)

    @router.get("/tools/audit-schedule")
    async def get_tool_audit_schedule(request: Request):
        await require_roles(request, HR_ALLOWED_ROLES)

        users = await db.users.find(
            {
                "is_active": True,
                "is_pin_user": True,
                "role": {"$in": list(TECHNICIAN_ROLES)},
            },
            {"_id": 0, "user_id": 1, "name": 1, "role": 1, "branch_id": 1},
        ).to_list(1000)

        result = []
        for user in users:
            last_audit = await db.hr_tool_audits.find_one(
                {"technician_id": user.get("user_id")},
                {"_id": 0, "created_at": 1, "status": 1, "next_due_at": 1},
                sort=[("created_at", -1)],
            )
            next_due = (last_audit or {}).get("next_due_at") or bi_monthly_next_due()
            next_due_dt = parse_iso(next_due)
            overdue = bool(next_due_dt and next_due_dt < datetime.now(timezone.utc))

            result.append(
                {
                    "technician_id": user.get("user_id"),
                    "technician_name": user.get("name"),
                    "role": user.get("role"),
                    "branch_id": user.get("branch_id"),
                    "last_audit_at": (last_audit or {}).get("created_at"),
                    "last_status": (last_audit or {}).get("status"),
                    "next_due_at": next_due,
                    "overdue": overdue,
                }
            )

        result.sort(key=lambda item: (not item.get("overdue"), item.get("technician_name") or ""))
        return result

    @router.get("/summary")
    async def get_hr_summary(request: Request):
        await require_roles(request, HR_ALLOWED_ROLES)

        now = datetime.now(timezone.utc)
        month_prefix = now.strftime("%Y-%m")
        month_range = {"$gte": f"{month_prefix}-01T00:00:00", "$lt": f"{month_prefix}-32T00:00:00"}

        clock_events = await db.hr_timeclock_events.count_documents({"created_at": month_range})
        leaves = await db.hr_leaves.count_documents({"created_at": month_range})
        adjustments = await db.hr_payroll_adjustments.find({"created_at": month_range}, {"_id": 0, "amount": 1}).to_list(5000)
        total_adjustments = sum(float(item.get("amount") or 0) for item in adjustments)
        expenses = await db.hr_operational_expenses.find({"created_at": month_range}, {"_id": 0, "amount": 1}).to_list(5000)
        total_expenses = sum(float(item.get("amount") or 0) for item in expenses)
        purchase_orders = await db.hr_purchase_orders.count_documents({"created_at": month_range})
        pending_tool_audits = await db.hr_tool_audits.count_documents({"status": "pending_deduction"})

        return {
            "month": month_prefix,
            "clock_events": clock_events,
            "leaves": leaves,
            "payroll_adjustments_total": total_adjustments,
            "operational_expenses_total": total_expenses,
            "purchase_orders": purchase_orders,
            "pending_tool_audits": pending_tool_audits,
        }

    return router
