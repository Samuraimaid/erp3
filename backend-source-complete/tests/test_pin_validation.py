import os
import uuid

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")


def create_auth_session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    r = s.post(f"{BASE_URL}/api/test/create-session")
    assert r.status_code == 200, f"Failed to create test session: {r.text}"
    token = r.json().get("session_token")
    assert token, "No session token returned"
    s.headers.update({"Authorization": f"Bearer {token}"})
    s.cookies.set("session_token", token)
    return s


def test_reject_empty_name():
    s = create_auth_session()
    payload = {
        "name": "",
        "role": "ventas",
        "pin": "1234",
        "login_pin": "12345678",
    }
    r = s.post(f"{BASE_URL}/api/users/pin", json=payload)
    assert r.status_code == 400, f"Expected 400 for empty name, got {r.status_code}: {r.text}"


def test_reject_invalid_phone_format():
    s = create_auth_session()
    unique_name = f"TEST_ValidName_{uuid.uuid4().hex[:6]}"
    payload = {
        "name": unique_name,
        "role": "ventas",
        "pin": "1234",
        "login_pin": "12345678",
        "phone": "1234",  # invalid format
    }
    r = s.post(f"{BASE_URL}/api/users/pin", json=payload)
    assert r.status_code == 400, f"Expected 400 for invalid phone, got {r.status_code}: {r.text}"
