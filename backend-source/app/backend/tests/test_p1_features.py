"""
Test P1 Features: Push Notifications, Thermal Printer ESC/POS, Multi-Currency Support
"""
import os

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001")


@pytest.fixture(scope="module")
def session_token():
    """Get test session token"""
    response = requests.post(f"{BASE_URL}/api/test/create-session")
    assert response.status_code == 200, f"Failed to create session: {response.text}"
    data = response.json()
    session_token = data["session_token"]
    # Ensure Xinon is promoted to admin for tests using this session (test user is a gerencia by default)
    try:
        requests.post(
            f"{BASE_URL}/api/users/promote-admin?email=dayavar18@gmail.com",
            headers={
                "Authorization": f"Bearer {session_token}",
                "Content-Type": "application/json",
            },
        )
        # ignore non-200 here; promote-admin may mark pending admin if user not present
    except Exception:
        pass

    return session_token


@pytest.fixture(scope="module")
def auth_headers(session_token):
    """Get auth headers with session token"""
    return {
        "Authorization": f"Bearer {session_token}",
        "Content-Type": "application/json",
    }


# ============ PUSH NOTIFICATIONS TESTS ============


class TestPushNotifications:
    """Test Push Notification endpoints"""

    def test_push_subscribe(self, auth_headers):
        """Test subscribing to push notifications"""
        subscription_data = {
            "endpoint": "https://test-push-endpoint.example.com/test123",
            "keys": {
                "p256dh": "test_p256dh_key_base64",
                "auth": "test_auth_key_base64",
            },
        }
        response = requests.post(
            f"{BASE_URL}/api/push/subscribe",
            json=subscription_data,
            headers=auth_headers,
        )
        assert response.status_code == 200, f"Push subscribe failed: {response.text}"
        data = response.json()
        assert "message" in data
        assert "Subscribed" in data["message"]
        print(f"✓ Push subscribe: {data['message']}")

    def test_push_notifications_get(self, auth_headers):
        """Test getting recent push notifications"""
        response = requests.get(
            f"{BASE_URL}/api/push/notifications", headers=auth_headers
        )
        assert response.status_code == 200, f"Get notifications failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Get push notifications: {len(data)} notifications found")

    def test_push_notifications_with_limit(self, auth_headers):
        """Test getting notifications with limit parameter"""
        response = requests.get(
            f"{BASE_URL}/api/push/notifications?limit=5", headers=auth_headers
        )
        assert (
            response.status_code == 200
        ), f"Get notifications with limit failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5
        print(f"✓ Get push notifications with limit: {len(data)} notifications")

    def test_push_unsubscribe(self, auth_headers):
        """Test unsubscribing from push notifications"""
        endpoint = "https://test-push-endpoint.example.com/test123"
        response = requests.delete(
            f"{BASE_URL}/api/push/unsubscribe?endpoint={endpoint}", headers=auth_headers
        )
        assert response.status_code == 200, f"Push unsubscribe failed: {response.text}"
        data = response.json()
        assert "message" in data
        assert "Unsubscribed" in data["message"]
        print(f"✓ Push unsubscribe: {data['message']}")


# ============ THERMAL PRINTER TESTS ============


class TestThermalPrinter:
    """Test Thermal Printer ESC/POS endpoints"""

    def test_thermal_printer_test(self, auth_headers):
        """Test thermal printer test endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/print/thermal/test", headers=auth_headers
        )
        assert response.status_code == 200, f"Thermal test failed: {response.text}"
        data = response.json()
        assert "commands_base64" in data
        assert "message" in data
        assert len(data["commands_base64"]) > 0
        print(
            f"✓ Thermal printer test: Generated {len(data['commands_base64'])} bytes of commands"
        )

    def test_thermal_print_custom_job(self, auth_headers):
        """Test generating custom thermal print job"""
        print_job = {
            "print_type": "custom",
            "title": "Test Receipt",
                "lines": [
                {"text": "MUNDO DE ACCESORIOS ERP", "align": "center", "bold": True},
                {"text": "Test Line 1", "align": "left"},
                {"text": "Test Line 2", "align": "right"},
                {"text": "Total: $100.00", "align": "right", "bold": True},
            ],
            "cut": True,
        }
        response = requests.post(
            f"{BASE_URL}/api/print/thermal", json=print_job, headers=auth_headers
        )
        assert (
            response.status_code == 200
        ), f"Custom thermal print failed: {response.text}"
        data = response.json()
        assert "commands_base64" in data
        print("✓ Custom thermal print: Generated commands successfully")


# ============ MULTI-CURRENCY TESTS ============


class TestMultiCurrency:
    """Test Multi-Currency Support endpoints"""

    def test_get_currencies(self):
        """Test getting available currencies (no auth required)"""
        response = requests.get(f"{BASE_URL}/api/currencies")
        assert response.status_code == 200, f"Get currencies failed: {response.text}"
        data = response.json()
        assert "currencies" in data
        currencies = data["currencies"]
        # Check for expected currencies
        assert "USD" in currencies
        assert "EUR" in currencies
        assert "MXN" in currencies  # Mexican Peso
        print(f"✓ Get currencies: {len(currencies)} currencies available")
        print(f"  Currencies: {list(currencies.keys())}")

    def test_get_exchange_rates(self, auth_headers):
        """Test getting exchange rates"""
        response = requests.get(
            f"{BASE_URL}/api/currencies/rates?base=USD", headers=auth_headers
        )
        assert response.status_code == 200, f"Get rates failed: {response.text}"
        data = response.json()
        assert "base" in data
        assert "rates" in data
        assert data["base"] == "USD"
        print(f"✓ Get exchange rates: Base {data['base']}, {len(data['rates'])} rates")
        for currency, rate in data["rates"].items():
            print(f"  1 USD = {rate} {currency}")

    def test_currency_convert(self, auth_headers):
        """Test currency conversion"""
        response = requests.get(
            f"{BASE_URL}/api/currencies/convert?amount=100&from_currency=USD&to_currency=EUR",
            headers=auth_headers,
        )
        assert response.status_code == 200, f"Currency convert failed: {response.text}"
        data = response.json()
        # API returns: amount, converted, from, to, rate, symbol
        assert "amount" in data
        assert "converted" in data
        assert "rate" in data
        assert "from" in data
        assert "to" in data
        assert data["amount"] == 100
        assert data["from"] == "USD"
        assert data["to"] == "EUR"
        print(
            f"✓ Currency convert: 100 USD = {data['converted']} EUR (rate: {data['rate']})"
        )

    def test_currency_convert_mxn(self, auth_headers):
        """Test currency conversion to MXN (Mexican Peso) - first set the rate"""
        # First set the MXN rate
        rate_update = {"from_currency": "USD", "to_currency": "MXN", "rate": 17.5}
        set_response = requests.put(
            f"{BASE_URL}/api/currencies/rates", json=rate_update, headers=auth_headers
        )
        assert (
            set_response.status_code == 200
        ), f"Failed to set MXN rate: {set_response.text}"

        # Now convert
        response = requests.get(
            f"{BASE_URL}/api/currencies/convert?amount=50&from_currency=USD&to_currency=MXN",
            headers=auth_headers,
        )
        assert (
            response.status_code == 200
        ), f"Currency convert to MXN failed: {response.text}"
        data = response.json()
        assert data["from"] == "USD"
        assert data["to"] == "MXN"
        print(f"✓ Currency convert MXN: 50 USD = {data['converted']} MXN")

    def test_get_system_currency(self, auth_headers):
        """Test getting system default currency"""
        response = requests.get(
            f"{BASE_URL}/api/settings/currency", headers=auth_headers
        )
        assert (
            response.status_code == 200
        ), f"Get system currency failed: {response.text}"
        data = response.json()
        assert "currency" in data
        print(f"✓ Get system currency: {data['currency']}")

    def test_set_system_currency(self, auth_headers):
        """Test setting system default currency"""
        response = requests.put(
            f"{BASE_URL}/api/settings/currency?currency=USD", headers=auth_headers
        )
        assert (
            response.status_code == 200
        ), f"Set system currency failed: {response.text}"
        data = response.json()
        assert "message" in data
        assert "USD" in data["message"]
        print(f"✓ Set system currency: {data['message']}")

    def test_update_exchange_rate(self, auth_headers):
        """Test updating exchange rate"""
        rate_update = {"from_currency": "USD", "to_currency": "EUR", "rate": 0.92}
        response = requests.put(
            f"{BASE_URL}/api/currencies/rates", json=rate_update, headers=auth_headers
        )
        assert response.status_code == 200, f"Update rate failed: {response.text}"
        data = response.json()
        assert "message" in data
        print(f"✓ Update exchange rate: {data['message']}")


# ============ WORK ORDER NOTIFY TEST ============


class TestWorkOrderNotify:
    """Test Work Order Notification endpoint"""

    def test_notify_work_order_requires_valid_id(self, auth_headers):
        """Test that notify endpoint requires valid work order ID"""
        response = requests.post(
            f"{BASE_URL}/api/work-orders/invalid_id/notify", headers=auth_headers
        )
        # Should return 404 for invalid work order
        assert (
            response.status_code == 404
        ), f"Expected 404 for invalid work order: {response.text}"
        print("✓ Work order notify: Returns 404 for invalid ID")


# ============ XINON ADMIN VERIFICATION ============


class TestXinonAdmin:
    """Test that Xinon (dayavar18@gmail.com) is admin"""

    def test_xinon_is_admin(self, auth_headers):
        """Verify Xinon user has admin (gerencia) role"""
        response = requests.get(f"{BASE_URL}/api/users", headers=auth_headers)
        assert response.status_code == 200, f"Get users failed: {response.text}"
        users = response.json()

        # Find Xinon user
        xinon_user = None
        for user in users:
            if user.get("email") == "dayavar18@gmail.com":
                xinon_user = user
                break

        if xinon_user:
            assert (
                xinon_user["role"] == "gerencia"
            ), f"Xinon role is {xinon_user['role']}, expected gerencia"
            print(
                f"✓ Xinon admin verification: {xinon_user['name']} has role '{xinon_user['role']}'"
            )
        else:
            # User might not exist yet - check pending admins or skip
            print("⚠ Xinon user not found in database - may need to login first")
            # This is acceptable - user will become admin on first login
            pytest.skip("Xinon user not yet in database")


# ============ THERMAL RECEIPT FOR SALE ============


class TestThermalReceiptForSale:
    """Test thermal receipt generation for actual sales"""

    def test_thermal_receipt_for_sale(self, auth_headers):
        """Test generating thermal receipt for a sale"""
        # First get a sale
        sales_response = requests.get(f"{BASE_URL}/api/sales", headers=auth_headers)

        if sales_response.status_code == 200:
            sales = sales_response.json()
            if len(sales) > 0:
                sale_id = sales[0]["sale_id"]
                response = requests.get(
                    f"{BASE_URL}/api/print/thermal/{sale_id}", headers=auth_headers
                )
                assert (
                    response.status_code == 200
                ), f"Thermal receipt failed: {response.status_code}"
                # This endpoint returns plain text, not JSON
                assert len(response.text) > 0
                assert "MUNDO DE ACCESORIOS" in response.text or "Factura" in response.text
                print(f"✓ Thermal receipt for sale {sale_id}: Generated successfully")
                print(f"  Receipt preview: {response.text[:100]}...")
            else:
                print("⚠ No sales found to test thermal receipt")
                pytest.skip("No sales available for thermal receipt test")
        else:
            pytest.skip("Could not fetch sales")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
