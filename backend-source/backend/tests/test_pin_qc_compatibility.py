"""
Test suite for PIN Authentication, Quality Control, and Vehicle Compatibility features.

Tests the following endpoints:
- PIN Auth: GET /api/auth/pin/users, POST /api/auth/pin/login,
  POST /api/users/pin, PUT /api/users/{id}/pin, DELETE /api/users/pin/{id}
- Quality Control: GET /api/quality-control, GET /api/quality-control/pending,
  POST /api/quality-control, GET /api/quality-control/stats/technicians,
  GET /api/quality-control/checklist-template
- Compatibility: GET /api/products/{id}/check-compatibility/{vehicle_id},
  POST /api/products/check-compatibility-batch
"""

import os
import uuid

import pytest
import requests
import random

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")


class TestSetup:
    """Setup test session and data"""

    @pytest.fixture(scope="class")
    def session(self):
        """Create authenticated session"""
        s = requests.Session()
        s.headers.update({"Content-Type": "application/json"})

        # Create test session
        response = s.post(f"{BASE_URL}/api/test/create-session")
        assert (
            response.status_code == 200
        ), f"Failed to create test session: {response.text}"

        data = response.json()
        session_token = data.get("session_token")
        assert session_token, "No session token returned"

        # Set auth header
        s.headers.update({"Authorization": f"Bearer {session_token}"})
        s.cookies.set("session_token", session_token)

        return s


class TestPinAuthentication(TestSetup):
    """Test PIN Authentication endpoints"""

    def test_get_pin_users_public(self, session):
        """GET /api/auth/pin/users - Public endpoint to list PIN users"""
        response = requests.get(f"{BASE_URL}/api/auth/pin/users")
        assert (
            response.status_code == 200
        ), f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()
        assert isinstance(data, list), "Expected list of PIN users"
        print(f"✓ GET /api/auth/pin/users - Found {len(data)} PIN users")

    def test_create_pin_user(self, session):
        """POST /api/users/pin - Create user with PIN (gerencia only)"""
        unique_name = f"TEST_PinUser_{uuid.uuid4().hex[:6]}"
        pin_data = {
            "name": unique_name,
            "role": "ventas",
            "pin": f"{random.randint(10**7, 10**8 - 1)}",
            "branch_id": None,
            "warehouse_id": None,
        }

        response = session.post(f"{BASE_URL}/api/users/pin", json=pin_data)
        assert (
            response.status_code == 200
        ), f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()
        assert "user_id" in data, "Response should contain user_id"
        assert data["name"] == unique_name, "Name should match"
        assert data["role"] == "ventas", "Role should be ventas"

        # Store for cleanup
        self.__class__.created_pin_user_id = data["user_id"]
        print(f"✓ POST /api/users/pin - Created PIN user: {data['user_id']}")
        return data["user_id"]

    def test_create_pin_user_invalid_pin(self, session):
        """POST /api/users/pin - Should reject invalid PIN (not 6 digits)"""
        pin_data = {
            "name": "Invalid PIN User",
            "role": "ventas",
            "pin": "12345",  # Only 5 digits (still invalid)
            "branch_id": None,
            "warehouse_id": None,
        }

        response = session.post(f"{BASE_URL}/api/users/pin", json=pin_data)
        assert (
            response.status_code == 400
        ), f"Expected 400 for invalid PIN, got {response.status_code}"
        print("✓ POST /api/users/pin - Correctly rejects invalid PIN")

    def test_create_pin_user_gerencia_role_rejected(self, session):
        """POST /api/users/pin - Gerencia PIN users are allowed (new requirement)"""
        pin_data = {
            "name": "Gerencia PIN User",
            "role": "gerencia",
            "pin": f"{random.randint(10**7, 10**8 - 1)}",
            "branch_id": None,
            "warehouse_id": None,
        }

        response = session.post(f"{BASE_URL}/api/users/pin", json=pin_data)
        assert (
            response.status_code == 200
        ), f"Expected 200 for gerencia PIN creation, got {response.status_code}: {response.text}"

        data = response.json()
        assert "user_id" in data, "Response should contain user_id"
        # Cleanup the created user
        session.delete(f"{BASE_URL}/api/users/pin/{data['user_id']}")
        print("✓ POST /api/users/pin - Created gerencia PIN user as configured")

    def test_pin_login(self, session):
        """POST /api/auth/pin/login - Login with PIN"""
        # First create a PIN user
        unique_name = f"TEST_LoginUser_{uuid.uuid4().hex[:6]}"
        attendance_pin = f"{random.randint(10**3, 10**4 - 1)}"
        test_pin = f"{random.randint(10**7, 10**8 - 1)}"
        pin_data = {
            "name": unique_name,
            "role": "ventas",
            "pin": attendance_pin,
            "login_pin": test_pin,
            "branch_id": None,
            "warehouse_id": None,
        }

        create_response = session.post(f"{BASE_URL}/api/users/pin", json=pin_data)
        assert (
            create_response.status_code == 200
        ), f"Failed to create PIN user: {create_response.text}"
        user_id = create_response.json()["user_id"]

        # Now login with PIN
        login_data = {"user_id": user_id, "pin": test_pin}

        login_response = requests.post(
            f"{BASE_URL}/api/auth/pin/login", json=login_data
        )
        assert (
            login_response.status_code == 200
        ), f"Expected 200, got {login_response.status_code}: {login_response.text}"

        data = login_response.json()
        user = data.get("user", data)
        assert user.get("user_id") == user_id, "User ID should match"
        assert user.get("name") == unique_name, "Name should match"
        print(f"✓ POST /api/auth/pin/login - Successfully logged in as {unique_name}")

        # Cleanup
        session.delete(f"{BASE_URL}/api/users/pin/{user_id}")

    def test_pin_login_wrong_pin(self, session):
        """POST /api/auth/pin/login - Should reject wrong PIN"""
        # First create a PIN user
        unique_name = f"TEST_WrongPinUser_{uuid.uuid4().hex[:6]}"
        attendance_pin = f"{random.randint(10**3, 10**4 - 1)}"
        test_pin = f"{random.randint(10**7, 10**8 - 1)}"
        pin_data = {
            "name": unique_name,
            "role": "ventas",
            "pin": attendance_pin,
            "login_pin": test_pin,
            "branch_id": None,
            "warehouse_id": None,
        }

        create_response = session.post(f"{BASE_URL}/api/users/pin", json=pin_data)
        assert create_response.status_code == 200
        user_id = create_response.json()["user_id"]

        # Try login with wrong PIN
        login_data = {"user_id": user_id, "pin": "00000000"}  # Wrong PIN (8 digits)

        login_response = requests.post(
            f"{BASE_URL}/api/auth/pin/login", json=login_data
        )
        assert (
            login_response.status_code == 401
        ), f"Expected 401 for wrong PIN, got {login_response.status_code}"
        print("✓ POST /api/auth/pin/login - Correctly rejects wrong PIN")

        # Cleanup
        session.delete(f"{BASE_URL}/api/users/pin/{user_id}")

    def test_update_pin(self, session):
        """PUT /api/users/{user_id}/pin - Update user PIN"""
        # First create a PIN user
        unique_name = f"TEST_UpdatePinUser_{uuid.uuid4().hex[:6]}"
        attendance_pin = f"{random.randint(10**3, 10**4 - 1)}"
        old_pin = f"{random.randint(10**7, 10**8 - 1)}"
        pin_data = {
            "name": unique_name,
            "role": "ventas",
            "pin": attendance_pin,
            "login_pin": old_pin,
            "branch_id": None,
            "warehouse_id": None,
        }

        create_response = session.post(f"{BASE_URL}/api/users/pin", json=pin_data)
        assert create_response.status_code == 200
        user_id = create_response.json()["user_id"]

        # Update PIN
        new_pin_val = f"{random.randint(10**7, 10**8 - 1)}"
        update_data = {"new_pin": new_pin_val}
        update_response = session.put(
            f"{BASE_URL}/api/users/{user_id}/login-pin", json=update_data
        )
        assert (
            update_response.status_code == 200
        ), f"Expected 200, got {update_response.status_code}: {update_response.text}"
        print(f"✓ PUT /api/users/{user_id}/login-pin - PIN updated successfully")

        # Verify new PIN works
        login_data = {"user_id": user_id, "pin": new_pin_val}
        login_response = requests.post(
            f"{BASE_URL}/api/auth/pin/login", json=login_data
        )
        assert login_response.status_code == 200, "New PIN should work"
        print("✓ Verified new PIN works after update")

        # Cleanup
        session.delete(f"{BASE_URL}/api/users/pin/{user_id}")

    def test_delete_pin_user(self, session):
        """DELETE /api/users/pin/{user_id} - Delete PIN user"""
        # First create a PIN user
        unique_name = f"TEST_DeleteUser_{uuid.uuid4().hex[:6]}"
        attendance_pin_del = f"{random.randint(10**3, 10**4 - 1)}"
        test_pin_del = f"{random.randint(10**7, 10**8 - 1)}"
        pin_data = {
            "name": unique_name,
            "role": "ventas",
            "pin": attendance_pin_del,
            "login_pin": test_pin_del,
            "branch_id": None,
            "warehouse_id": None,
        }

        create_response = session.post(f"{BASE_URL}/api/users/pin", json=pin_data)
        assert create_response.status_code == 200
        user_id = create_response.json()["user_id"]

        # Delete user
        delete_response = session.delete(f"{BASE_URL}/api/users/pin/{user_id}")
        assert (
            delete_response.status_code == 200
        ), f"Expected 200, got {delete_response.status_code}: {delete_response.text}"
        print(f"✓ DELETE /api/users/pin/{user_id} - User deleted successfully")

        # Verify user cannot login anymore
        login_data = {"user_id": user_id, "pin": test_pin_del}
        login_response = requests.post(
            f"{BASE_URL}/api/auth/pin/login", json=login_data
        )
        assert (
            login_response.status_code == 401
        ), "Deleted user should not be able to login"
        print("✓ Verified deleted user cannot login")


class TestQualityControl(TestSetup):
    """Test Quality Control endpoints"""

    def test_get_quality_controls(self, session):
        """GET /api/quality-control - List quality control inspections"""
        response = session.get(f"{BASE_URL}/api/quality-control")
        assert (
            response.status_code == 200
        ), f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()
        assert isinstance(data, list), "Expected list of QC records"
        print(f"✓ GET /api/quality-control - Found {len(data)} QC records")

    def test_get_pending_orders(self, session):
        """GET /api/quality-control/pending - Get orders pending QC inspection"""
        response = session.get(f"{BASE_URL}/api/quality-control/pending")
        assert (
            response.status_code == 200
        ), f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()
        assert isinstance(data, list), "Expected list of pending orders"
        print(f"✓ GET /api/quality-control/pending - Found {len(data)} pending orders")

    def test_get_checklist_template(self, session):
        """GET /api/quality-control/checklist-template - Get QC checklist template"""
        response = session.get(f"{BASE_URL}/api/quality-control/checklist-template")
        assert (
            response.status_code == 200
        ), f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()
        assert "categories" in data, "Response should contain categories"
        assert isinstance(data["categories"], list), "Categories should be a list"

        # Verify template structure
        if len(data["categories"]) > 0:
            category = data["categories"][0]
            assert "name" in category, "Category should have name"
            assert "items" in category, "Category should have items"

        print(
            f"✓ GET /api/quality-control/checklist-template - Found {len(data['categories'])} categories"
        )

    def test_get_technician_stats(self, session):
        """GET /api/quality-control/stats/technicians - Get technician performance stats"""
        response = session.get(f"{BASE_URL}/api/quality-control/stats/technicians")
        assert (
            response.status_code == 200
        ), f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()
        assert isinstance(data, list), "Expected list of technician stats"

        # Verify stats structure if data exists
        if len(data) > 0:
            stat = data[0]
            expected_fields = [
                "technician_id",
                "technician_name",
                "total_inspections",
                "average_rating",
            ]
            for field in expected_fields:
                assert field in stat, f"Stat should contain {field}"

        print(
            f"✓ GET /api/quality-control/stats/technicians - Found {len(data)} technician stats"
        )

    def test_create_quality_control_requires_work_order(self, session):
        """POST /api/quality-control - Should require valid work order"""
        qc_data = {
            "work_order_id": "invalid_wo_id",
            "overall_rating": 4,
            "cleanliness_rating": 4,
            "functionality_rating": 4,
            "finish_rating": 4,
            "safety_rating": 4,
            "checklist": [],
            "comments": "Test QC",
            "approved": True,
        }

        response = session.post(f"{BASE_URL}/api/quality-control", json=qc_data)
        # Should fail because work order doesn't exist
        assert response.status_code in [
            400,
            404,
        ], f"Expected 400/404 for invalid work order, got {response.status_code}"
        print("✓ POST /api/quality-control - Correctly requires valid work order")


class TestVehicleCompatibility(TestSetup):
    """Test Vehicle Compatibility endpoints"""

    @pytest.fixture(scope="class")
    def test_data(self, session):
        """Create test customer, vehicle, and product for compatibility tests"""
        # Create test customer
        customer_data = {
            "name": f"TEST_CompatCustomer_{uuid.uuid4().hex[:6]}",
            "phone": "555-0123",
            "email": "test@compat.com",
        }
        customer_response = session.post(
            f"{BASE_URL}/api/customers", json=customer_data
        )
        assert (
            customer_response.status_code == 200
        ), f"Failed to create customer: {customer_response.text}"
        customer_id = customer_response.json()["customer_id"]

        # Create test vehicle
        vehicle_data = {
            "customer_id": customer_id,
            "plate": f"TEST{uuid.uuid4().hex[:4].upper()}",
            "brand": "Toyota",
            "model": "Corolla",
            "year": 2020,
            "vehicle_type": "Sedán",
        }
        vehicle_response = session.post(f"{BASE_URL}/api/vehicles", json=vehicle_data)
        assert (
            vehicle_response.status_code == 200
        ), f"Failed to create vehicle: {vehicle_response.text}"
        vehicle_id = vehicle_response.json()["vehicle_id"]

        # Create test product with compatibility restrictions
        product_data = {
            "sku": f"TEST-COMPAT-{uuid.uuid4().hex[:6]}",
            "name": "Test Compatible Product",
            "category": "accesorios_no_electricos",
            "subcategory": "Defensas",
            "brand": "TestBrand",
            "price": 100.0,
            "cost": 50.0,
            "compatibility": {
                "brands": ["Toyota", "Honda"],
                "models": ["Corolla", "Civic"],
                "year_from": 2018,
                "year_to": 2025,
                "vehicle_types": ["Sedán", "Hatchback"],
            },
        }
        product_response = session.post(f"{BASE_URL}/api/products", json=product_data)
        assert (
            product_response.status_code == 200
        ), f"Failed to create product: {product_response.text}"
        product_id = product_response.json()["product_id"]

        # Create incompatible product
        incompatible_product_data = {
            "sku": f"TEST-INCOMPAT-{uuid.uuid4().hex[:6]}",
            "name": "Test Incompatible Product",
            "category": "accesorios_no_electricos",
            "subcategory": "Defensas",
            "brand": "TestBrand",
            "price": 150.0,
            "cost": 75.0,
            "compatibility": {
                "brands": ["Ford", "Chevrolet"],
                "models": ["F-150", "Silverado"],
                "year_from": 2015,
                "year_to": 2020,
                "vehicle_types": ["Pickup"],
            },
        }
        incompatible_response = session.post(
            f"{BASE_URL}/api/products", json=incompatible_product_data
        )
        assert incompatible_response.status_code == 200
        incompatible_product_id = incompatible_response.json()["product_id"]

        return {
            "customer_id": customer_id,
            "vehicle_id": vehicle_id,
            "product_id": product_id,
            "incompatible_product_id": incompatible_product_id,
        }

    def test_check_compatibility_compatible(self, session, test_data):
        """GET /api/products/{id}/check-compatibility/{vehicle_id} - Compatible product"""
        product_id = test_data["product_id"]
        vehicle_id = test_data["vehicle_id"]

        response = session.get(
            f"{BASE_URL}/api/products/{product_id}/check-compatibility/{vehicle_id}"
        )
        assert (
            response.status_code == 200
        ), f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()
        assert "compatible" in data, "Response should contain compatible field"
        assert data["compatible"] is True, f"Product should be compatible: {data}"
        print(
            f"✓ GET /api/products/{product_id}/check-compatibility/{vehicle_id} - Product is compatible"
        )

    def test_check_compatibility_incompatible(self, session, test_data):
        """GET /api/products/{id}/check-compatibility/{vehicle_id} - Incompatible product"""
        product_id = test_data["incompatible_product_id"]
        vehicle_id = test_data["vehicle_id"]

        response = session.get(
            f"{BASE_URL}/api/products/{product_id}/check-compatibility/{vehicle_id}"
        )
        assert (
            response.status_code == 200
        ), f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()
        assert "compatible" in data, "Response should contain compatible field"
        assert data["compatible"] is False, f"Product should be incompatible: {data}"
        assert "reasons" in data, "Response should contain reasons"
        print(
            f"✓ GET /api/products/{product_id}/check-compatibility/{vehicle_id} - Product is incompatible"
        )
        print(f"  Reasons: {data.get('reasons')}")

    def test_check_compatibility_batch(self, session, test_data):
        """POST /api/products/check-compatibility-batch - Check multiple products"""
        vehicle_id = test_data["vehicle_id"]
        product_ids = [test_data["product_id"], test_data["incompatible_product_id"]]

        response = session.post(
            f"{BASE_URL}/api/products/check-compatibility-batch",
            params={"vehicle_id": vehicle_id},
            json=product_ids,
        )
        assert (
            response.status_code == 200
        ), f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()
        assert "results" in data, "Response should contain results"
        assert "summary" in data, "Response should contain summary"
        assert len(data["results"]) == 2, "Should have 2 results"

        # Verify summary
        summary = data["summary"]
        assert summary["total"] == 2, "Total should be 2"
        assert summary["compatible"] == 1, "Should have 1 compatible"
        assert summary["incompatible"] == 1, "Should have 1 incompatible"

        print(
            f"✓ POST /api/products/check-compatibility-batch - Batch check: {summary}"
        )

    def test_check_compatibility_invalid_product(self, session, test_data):
        """GET /api/products/{id}/check-compatibility/{vehicle_id} - Invalid product"""
        vehicle_id = test_data["vehicle_id"]

        response = session.get(
            f"{BASE_URL}/api/products/invalid_product_id/check-compatibility/{vehicle_id}"
        )
        assert (
            response.status_code == 404
        ), f"Expected 404 for invalid product, got {response.status_code}"
        print(
            "✓ GET /api/products/invalid/check-compatibility - Returns 404 for invalid product"
        )

    def test_check_compatibility_invalid_vehicle(self, session, test_data):
        """GET /api/products/{id}/check-compatibility/{vehicle_id} - Invalid vehicle"""
        product_id = test_data["product_id"]

        response = session.get(
            f"{BASE_URL}/api/products/{product_id}/check-compatibility/invalid_vehicle_id"
        )
        assert (
            response.status_code == 404
        ), f"Expected 404 for invalid vehicle, got {response.status_code}"
        print(
            "✓ GET /api/products/{id}/check-compatibility/invalid - Returns 404 for invalid vehicle"
        )


class TestAuthRequirements(TestSetup):
    """Test that endpoints require proper authentication"""

    def test_pin_user_creation_requires_auth(self):
        """POST /api/users/pin - Should require authentication"""
        pin_data = {"name": "Unauthorized User", "role": "ventas", "pin": "12345678"}

        response = requests.post(f"{BASE_URL}/api/users/pin", json=pin_data)
        assert (
            response.status_code == 401
        ), f"Expected 401 without auth, got {response.status_code}"
        print("✓ POST /api/users/pin - Requires authentication")

    def test_quality_control_requires_auth(self):
        """GET /api/quality-control - Should require authentication"""
        response = requests.get(f"{BASE_URL}/api/quality-control")
        assert (
            response.status_code == 401
        ), f"Expected 401 without auth, got {response.status_code}"
        print("✓ GET /api/quality-control - Requires authentication")

    def test_compatibility_check_requires_auth(self):
        """GET /api/products/{id}/check-compatibility/{vehicle_id} - Should require authentication"""
        response = requests.get(
            f"{BASE_URL}/api/products/test/check-compatibility/test"
        )
        assert (
            response.status_code == 401
        ), f"Expected 401 without auth, got {response.status_code}"
        print("✓ GET /api/products/{id}/check-compatibility - Requires authentication")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
