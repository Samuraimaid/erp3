from __future__ import annotations

from typing import Any, Dict
import os


class PinPolicyService:
    def __init__(self, db, logger):
        self.db = db
        self.logger = logger

    def defaults(self) -> Dict[str, Any]:
        return {
            "max_attempts": int(os.environ.get("PIN_MAX_ATTEMPTS", "5")),
            "lockout_minutes": int(os.environ.get("PIN_LOCKOUT_MIN", "15")),
            "lockout_seconds": int(os.environ.get("PIN_LOCKOUT_S", "30")),
            "pin_expiry_days": int(os.environ.get("PIN_EXPIRY_DAYS", "90")),
            "pin_rotation_days": int(os.environ.get("PIN_ROTATION_DAYS", "60")),
            "enforce_rotation": os.environ.get("PIN_ROTATION_ENFORCE", "false").lower() in ("1", "true", "yes"),
            "ip_window_seconds": int(os.environ.get("PIN_IP_WINDOW_S", "60")),
            "ip_max_attempts": int(os.environ.get("PIN_IP_MAX", "20")),
            "allow_legacy_sha": os.environ.get("PIN_ALLOW_LEGACY_SHA", "true").lower() in ("1", "true", "yes"),
        }

    def normalize(self, policy: Dict[str, Any]) -> Dict[str, Any]:
        defaults = self.defaults()
        merged = {**defaults, **{k: v for k, v in policy.items() if k in defaults}}
        merged["max_attempts"] = max(1, int(merged["max_attempts"]))
        merged["lockout_minutes"] = max(0, int(merged["lockout_minutes"]))
        merged["lockout_seconds"] = max(0, int(merged.get("lockout_seconds", 0)))
        merged["pin_expiry_days"] = int(merged["pin_expiry_days"])
        merged["pin_rotation_days"] = int(merged["pin_rotation_days"])
        merged["ip_window_seconds"] = max(1, int(merged["ip_window_seconds"]))
        merged["ip_max_attempts"] = max(1, int(merged["ip_max_attempts"]))
        merged["enforce_rotation"] = bool(merged["enforce_rotation"])
        merged["allow_legacy_sha"] = bool(merged["allow_legacy_sha"])
        return merged

    async def load(self) -> Dict[str, Any]:
        try:
            policy_doc = await self.db.settings.find_one({"type": "pin_policy"}, {"_id": 0})
            if not policy_doc:
                defaults = self.defaults()
                await self.db.settings.update_one(
                    {"type": "pin_policy"},
                    {"$set": {"type": "pin_policy", **defaults}},
                    upsert=True,
                )
                return defaults
            return self.normalize(policy_doc)
        except Exception:
            self.logger.exception("Failed to load pin policy, falling back to defaults")
            return self.defaults()

    async def update(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        current = await self.load()
        merged = self.normalize({**current, **updates})
        await self.db.settings.update_one(
            {"type": "pin_policy"},
            {"$set": {"type": "pin_policy", **merged}},
            upsert=True,
        )
        return merged
