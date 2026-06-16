import os
import requests
import time
import random

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:8001")


def admin_headers():
    # Create a test admin session using test endpoint (ENABLE_TEST_ENDPOINTS=true)
    r = requests.post(f"{BASE_URL}/api/test/create-session")
    r.raise_for_status()
    # cookies from response
    return {"Cookie": f"session_token={r.cookies.get('session_token')}"}


def test_pin_create_and_login_flow():
    hdrs = admin_headers()

    # create pin user with attendance PIN (4) and login PIN (8)
    attendance_pin = f"{random.randint(10**3, 10**4 - 1)}"
    login_pin = f"{random.randint(10**7, 10**8 - 1)}"
    payload = {
        "name": "integ_pin_user",
        "last_name": "integration",
        "phone": "5555-1111",
        "role": "instalaciones",
        "pin": attendance_pin,
        "login_pin": login_pin,
        "branch_id": "branch_test",
    }
    r = requests.post(f"{BASE_URL}/api/users/pin", json=payload, headers=hdrs)
    r.raise_for_status()
    user = r.json()
    assert "user_id" in user
    user_id = user["user_id"]

    # attempt wrong pin
    r = requests.post(f"{BASE_URL}/api/auth/pin/login", json={"user_id": user_id, "pin": "00000000"})
    assert r.status_code == 401

    # correct pin
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/pin/login", json={"user_id": user_id, "pin": login_pin})
    assert r.status_code == 200
    data = r.json()
    # API returns {"user": {...}, "session_token": "..."}
    assert data.get("user", {}).get("name") == "integ_pin_user"

    # admin resets pin
    r = requests.post(f"{BASE_URL}/api/users/{user_id}/pin/reset", json={}, headers=hdrs)
    r.raise_for_status()
    reset = r.json()
    assert "new_pin" in reset
    new_pin = reset["new_pin"]

    # old pin should fail
    r = requests.post(f"{BASE_URL}/api/auth/pin/login", json={"user_id": user_id, "pin": login_pin})
    assert r.status_code == 401

    # new pin should work
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/pin/login", json={"user_id": user_id, "pin": new_pin})
    assert r.status_code == 200

    # cleanup
    requests.delete(f"{BASE_URL}/api/users/pin/{user_id}", headers=hdrs)
