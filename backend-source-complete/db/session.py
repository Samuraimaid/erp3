from __future__ import annotations

import os
from typing import Any

from pymongo import MongoClient


MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
MONGO_DB = os.environ.get("MONGO_DB", os.environ.get("DB_NAME", "mc-larens2_erp"))

_client = MongoClient(MONGO_URL)
_db = _client[MONGO_DB]


def get_collection(name: str) -> Any:
    return _db[name]
