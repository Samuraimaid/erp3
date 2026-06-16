from __future__ import annotations

from typing import Any, Dict, Optional


class CashService:
    def __init__(self, db, logger):
        self.db = db
        self.logger = logger

    async def get_default_currency(self) -> str:
        settings = await self.db.settings.find_one({"type": "system"}, {"_id": 0})
        return settings.get("default_currency", "USD") if settings else "USD"

    async def calculate_cash_sales_total(
        self, branch_id: Optional[str], start_iso: str, end_iso: str
    ) -> Dict[str, Any]:
        query: Dict[str, Any] = {
            "payment_type": "cash",
            "created_at": {"$gte": start_iso, "$lte": end_iso},
        }
        if branch_id:
            query["branch_id"] = branch_id
        sales = await self.db.sales.find(query, {"_id": 0, "total": 1}).to_list(10000)
        total = round(sum((s.get("total") or 0) for s in sales), 2)
        return {"cash_sales_total": total, "cash_sales_count": len(sales)}
