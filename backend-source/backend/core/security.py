from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    id: str
    role: str
    branch_id: str = "branch_main"
    name: str = "Usuario"


def get_current_user() -> User:
    return User(
        id=os.environ.get("DEFAULT_USER_ID", "gerente-1"),
        role=os.environ.get("DEFAULT_USER_ROLE", "gerencia"),
        branch_id=os.environ.get("DEFAULT_BRANCH_ID", "branch_main"),
        name=os.environ.get("DEFAULT_USER_NAME", "Gerencia"),
    )


def get_user_by_token(token: Optional[str]) -> Optional[User]:
    if token is None:
        return None
    return get_current_user()


def verify_manager_pin(user_id: str, pin: str) -> bool:
    expected_pin = os.environ.get("MANAGER_PIN", "12345678")
    return bool(user_id) and pin == expected_pin


def verify_cajero_pin(user_id: str, pin: str) -> bool:
    expected_pin = os.environ.get("CAJERO_PIN", "1234")
    return bool(user_id) and pin == expected_pin
