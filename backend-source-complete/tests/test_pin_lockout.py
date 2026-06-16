import os
import requests
import random
from datetime import datetime

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:8001")


def admin_headers():
    r = requests.post(f"{BASE_URL}/api/test/create-session")
    r.raise_for_status()
    return {"Cookie": f"session_token={r.cookies.get('session_token')}"}


def test_pin_lockout_after_max_attempts():
    hdrs = admin_headers()

    # create a pin user with attendance PIN (4) and login PIN (8)
    attendance_pin = f"{random.randint(10**3, 10**4 - 1)}"
    login_pin = f"{random.randint(10**7, 10**8 - 1)}"
    payload = {
        "name": "lockout_user",
        "last_name": "lockout",
        "phone": "5555-2222",
        "role": "ventas",
        "pin": attendance_pin,
        "login_pin": login_pin,
        "branch_id": "branch_test",
    }
    r = requests.post(f"{BASE_URL}/api/users/pin", json=payload, headers=hdrs)
    r.raise_for_status()
    user = r.json()
    user_id = user.get("user_id")
    assert user_id

    wrong_pin = "00000000"
    MAX_ATTEMPTS = 5

    # perform MAX_ATTEMPTS - 1 failures and assert 401 + remaining_attempts provided
    for i in range(1, MAX_ATTEMPTS):
        r = requests.post(f"{BASE_URL}/api/auth/pin/login", json={"user_id": user_id, "pin": wrong_pin})
        assert r.status_code == 401
        body = r.json()
        detail = body.get("detail") if isinstance(body, dict) else None
        if isinstance(detail, dict) and detail.get("remaining_attempts") is not None:
            remaining_attempts = detail.get("remaining_attempts")
            assert isinstance(remaining_attempts, int)
            assert remaining_attempts >= 0

    # final failing attempt should produce a 403 lockout response
    r = requests.post(f"{BASE_URL}/api/auth/pin/login", json={"user_id": user_id, "pin": wrong_pin})
    assert r.status_code == 403
    body = r.json()
    detail = body.get("detail") if isinstance(body, dict) else None
    assert isinstance(detail, dict), f"expected structured detail in 403 response, got: {body}"
    assert detail.get("remaining_attempts") == 0
    assert detail.get("lockout_until") is not None

    # cleanup
    requests.delete(f"{BASE_URL}/api/users/pin/{user_id}", headers=hdrs)
