"""Integration tests for technicians CRUD flow.

These tests exercise the /api/technicians endpoints using the test session
endpoint for authentication. They are idempotent and safe to run repeatedly.
"""

import os
import uuid

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")


class TestTechniciansCRUD:
    @pytest.fixture(autouse=True)
    def setup(self):
        # Create test session and store cookies
        response = requests.post(
            f"{BASE_URL}/api/test/create-session",
            json={"email": "test.admin@mundodeaccesorios.com", "name": "Test Admin", "role": "gerencia"},
        )
        assert response.status_code == 200, f"Failed to create session: {response.text}"
        data = response.json()
        self.cookies = {"session_token": data.get("session_token")}
        yield

    def test_technicians_crud_flow(self):
        # List technicians (should be a list)
        r = requests.get(f"{BASE_URL}/api/technicians", cookies=self.cookies)
        assert r.status_code == 200, r.text
        techs = r.json()
        assert isinstance(techs, list)

        # Prepare a unique technician email
        unique = uuid.uuid4().hex[:8]
        email = f"tec_test_{unique}@example.com"

        # Ensure no leftover with same email
        existing = [t for t in techs if t.get("email") == email]
        if existing:
            # delete leftovers
            for t in existing:
                requests.delete(f"{BASE_URL}/api/technicians/{t['user_id']}", cookies=self.cookies)

        # Create technician
        payload = {"email": email, "name": "Técnico Test", "specialty": "electrico"}
        r = requests.post(f"{BASE_URL}/api/technicians", json=payload, cookies=self.cookies)
        assert r.status_code == 200, f"Create failed: {r.status_code} {r.text}"
        created = r.json()
        assert created.get("email") == email
        user_id = created.get("user_id")
        assert user_id

        # Verify present in list
        r = requests.get(f"{BASE_URL}/api/technicians", cookies=self.cookies)
        assert r.status_code == 200
        found = [t for t in r.json() if t.get("email") == email]
        assert len(found) == 1

        # Update technician
        update_payload = {"name": "Técnico Test Updated", "specialty": "instalador"}
        r = requests.put(f"{BASE_URL}/api/technicians/{user_id}", json=update_payload, cookies=self.cookies)
        assert r.status_code == 200, f"Update failed: {r.status_code} {r.text}"
        updated = r.json()
        assert updated.get("name") == "Técnico Test Updated"
        assert updated.get("specialty") == "instalador"

        # Delete technician
        r = requests.delete(f"{BASE_URL}/api/technicians/{user_id}", cookies=self.cookies)
        assert r.status_code == 200, f"Delete failed: {r.status_code} {r.text}"

        # Verify deletion
        r = requests.get(f"{BASE_URL}/api/technicians", cookies=self.cookies)
        assert r.status_code == 200
        remaining = [t for t in r.json() if t.get("email") == email]
        assert len(remaining) == 0
