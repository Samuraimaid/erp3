from backend.db.session import get_collection
from datetime import datetime

def cleanup_tokens(terminal_id: str):
    tokens = get_collection("auth_tokens")
    tokens.delete_many({"terminal_id": terminal_id})
    return True

def cleanup_tokens_end_of_day():
    tokens = get_collection("auth_tokens")
    now = datetime.utcnow()
    tokens.delete_many({"expires_at": {"$lte": now}})
