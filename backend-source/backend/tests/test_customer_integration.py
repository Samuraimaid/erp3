import os
import requests
import time

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:8001")


def admin_headers():
    r = requests.post(f"{BASE_URL}/api/test/create-session")
    r.raise_for_status()
    return {"Cookie": f"session_token={r.cookies.get('session_token')}"}


def test_create_customer_appears_in_list():
    hdrs = admin_headers()
    payload = {
        "name": "integ_test_customer",
        "email": "integ_customer@example.com",
        "phone": "7777-8888",
        "address": "Prueba 123",
    }
    r = requests.post(f"{BASE_URL}/api/customers", json=payload, headers=hdrs)
    r.raise_for_status()
    created = r.json()
    assert "customer_id" in created
    cid = created["customer_id"]

    # small pause then fetch list
    time.sleep(0.2)
    r = requests.get(f"{BASE_URL}/api/customers", headers=hdrs)
    r.raise_for_status()
    customers = r.json()
    assert any(c.get("customer_id") == cid for c in customers), f"Created {cid} not present in customers list"
