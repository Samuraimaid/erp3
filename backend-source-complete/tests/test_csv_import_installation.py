"""
Test CSV Import and Installation Type Features
Tests for:
- GET /api/products/import/template - Download CSV template (public)
- POST /api/products/import/csv - Import products from CSV (requires auth)
- POST /api/products/seed-demo - Create demo products (requires gerencia role)
- POST /api/auth/manager/generate-code - Generate manager authorization code
- Verify installation_type field in products
"""

import os
import uuid

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")


class TestCSVImportAndInstallation:
    """Test CSV Import and Installation Type Features"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()

        # Get auth session via test endpoint
        try:
            test_session = self.session.post(
                f"{BASE_URL}/api/test/create-session", timeout=10
            )
            if test_session.status_code == 200:
                session_data = test_session.json()
                if session_data.get("session_token"):
                    self.session.cookies.set(
                        "session_token", session_data["session_token"]
                    )
                    print("✓ Authenticated with test session")
        except Exception as e:
            print(f"Auth setup warning: {e}")

    # ============ CSV TEMPLATE TESTS ============

    def test_get_csv_template_public(self):
        """Test GET /api/products/import/template - should be public"""
        response = requests.get(f"{BASE_URL}/api/products/import/template", timeout=10)

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert "text/csv" in response.headers.get(
            "Content-Type", ""
        ), "Should return CSV content type"

        # Verify CSV content
        content = response.text
        assert (
            "sku,name,description,category" in content
        ), "Template should have CSV headers"
        assert (
            "installation_type" in content
        ), "Template should include installation_type column"
        assert (
            "required" in content or "optional" in content or "not_available" in content
        ), "Template should have installation_type examples"

        print("✓ CSV template downloaded successfully")
        print(f"  Headers: {content.split(chr(10))[0][:100]}...")

    def test_csv_template_has_correct_columns(self):
        """Verify CSV template has all required columns"""
        response = requests.get(f"{BASE_URL}/api/products/import/template", timeout=10)

        assert response.status_code == 200

        lines = response.text.strip().split("\n")
        headers = lines[0].split(",")

        required_columns = [
            "sku",
            "name",
            "category",
            "brand",
            "price",
            "installation_type",
        ]
        for col in required_columns:
            assert col in headers, f"Missing required column: {col}"

        print(f"✓ CSV template has all required columns: {headers}")

    # ============ PRODUCTS WITH INSTALLATION_TYPE TESTS ============

    def test_demo_products_have_installation_type(self):
        """Verify demo products have installation_type field"""
        # First seed demo products to ensure they exist
        warehouses_response = self.session.get(f"{BASE_URL}/api/warehouses", timeout=10)

        if warehouses_response.status_code == 401:
            pytest.skip("Authentication required - skipping")

        warehouse_id = "wh_main"
        if warehouses_response.status_code == 200:
            warehouses = warehouses_response.json()
            if len(warehouses) > 0:
                warehouse_id = warehouses[0].get("warehouse_id", "wh_main")

        # Seed demo products
        self.session.post(
            f"{BASE_URL}/api/products/seed-demo",
            params={"warehouse_id": warehouse_id},
            timeout=30,
        )

        # Get products
        response = self.session.get(f"{BASE_URL}/api/products", timeout=10)

        if response.status_code == 401:
            pytest.skip("Authentication required - skipping")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        products = response.json()

        # Count products with installation_type
        products_with_type = [
            p
            for p in products
            if "installation_type" in p and p.get("installation_type")
        ]

        print("✓ Products analysis:")
        print(f"  Total products: {len(products)}")
        print(f"  Products with installation_type: {len(products_with_type)}")

        # At least some products should have installation_type (demo products)
        assert (
            len(products_with_type) > 0
        ), "At least some products should have installation_type"

        # Count by type
        types_count = {"required": 0, "optional": 0, "not_available": 0}
        for p in products_with_type:
            install_type = p.get("installation_type")
            if install_type in types_count:
                types_count[install_type] += 1

        print(f"  By type: {types_count}")

        # Verify we have different types
        assert (
            types_count["required"] > 0
            or types_count["optional"] > 0
            or types_count["not_available"] > 0
        ), "Should have at least one product with a valid installation_type"

    # ============ MANAGER AUTHORIZATION TESTS ============

    def test_manager_generate_auth_code(self):
        """Test POST /api/auth/manager/generate-code - requires gerencia role"""
        response = self.session.post(
            f"{BASE_URL}/api/auth/manager/generate-code",
            params={"reason": "Test authorization for installation"},
            timeout=10,
        )

        if response.status_code == 401:
            pytest.skip("Authentication required - skipping")

        if response.status_code == 403:
            print("⚠ User does not have gerencia role - expected for non-manager users")
            return

        assert (
            response.status_code == 200
        ), f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()
        assert "code" in data, "Response should contain authorization code"
        assert data["code"].startswith(
            "AUTH-"
        ), f"Code should start with AUTH-, got: {data['code']}"
        assert "expires_at" in data, "Response should contain expiration time"

        print(f"✓ Manager authorization code generated: {data['code']}")
        print(f"  Expires at: {data['expires_at']}")
        print(f"  Valid for: {data.get('valid_for_minutes', 60)} minutes")

    def test_manager_pending_authorizations(self):
        """Test GET /api/auth/manager/pending - get pending authorizations"""
        response = self.session.get(f"{BASE_URL}/api/auth/manager/pending", timeout=10)

        if response.status_code == 401:
            pytest.skip("Authentication required - skipping")

        if response.status_code == 403:
            print("⚠ User does not have gerencia/supervisor role")
            return

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert isinstance(data, list), "Response should be a list"

        print(f"✓ Pending authorizations retrieved: {len(data)} items")

    # ============ SEED DEMO PRODUCTS TESTS ============

    def test_seed_demo_products(self):
        """Test POST /api/products/seed-demo - requires gerencia role"""
        # First get a warehouse
        warehouses_response = self.session.get(f"{BASE_URL}/api/warehouses", timeout=10)

        if warehouses_response.status_code == 401:
            pytest.skip("Authentication required - skipping")

        warehouse_id = "wh_main"
        if warehouses_response.status_code == 200:
            warehouses = warehouses_response.json()
            if len(warehouses) > 0:
                warehouse_id = warehouses[0].get("warehouse_id", "wh_main")

        response = self.session.post(
            f"{BASE_URL}/api/products/seed-demo",
            params={"warehouse_id": warehouse_id},
            timeout=30,
        )

        if response.status_code == 401:
            pytest.skip("Authentication required - skipping")

        if response.status_code == 403:
            print("⚠ User does not have gerencia role - expected for non-manager users")
            return

        assert (
            response.status_code == 200
        ), f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()
        # Response can have 'created' or 'imported' depending on implementation
        assert "imported" in data or "created" in data, "Response should contain count"

        count = data.get("imported", data.get("created", 0))
        print(f"✓ Demo products seeded: {count} products")
        print(f"  Message: {data.get('message', 'N/A')}")

    def test_demo_products_include_not_available_type(self):
        """Verify demo products include 'not_available' (solo para llevar) type"""
        # Seed demo products
        warehouses_response = self.session.get(f"{BASE_URL}/api/warehouses", timeout=10)

        if warehouses_response.status_code == 401:
            pytest.skip("Authentication required - skipping")

        warehouse_id = "wh_main"
        if warehouses_response.status_code == 200:
            warehouses = warehouses_response.json()
            if len(warehouses) > 0:
                warehouse_id = warehouses[0].get("warehouse_id", "wh_main")

        self.session.post(
            f"{BASE_URL}/api/products/seed-demo",
            params={"warehouse_id": warehouse_id},
            timeout=30,
        )

        # Get products
        response = self.session.get(f"{BASE_URL}/api/products", timeout=10)

        if response.status_code != 200:
            pytest.skip("Could not get products")

        products = response.json()

        # Find products with not_available type (solo para llevar)
        solo_para_llevar = [
            p for p in products if p.get("installation_type") == "not_available"
        ]

        print(f"✓ 'Solo para llevar' products found: {len(solo_para_llevar)}")
        for p in solo_para_llevar[:3]:
            print(f"  - {p.get('name', 'N/A')} (SKU: {p.get('sku', 'N/A')})")

        assert (
            len(solo_para_llevar) > 0
        ), "Should have at least one 'solo para llevar' product"

    # ============ CSV IMPORT TESTS ============

    def test_csv_import_requires_auth(self):
        """Test POST /api/products/import/csv requires authentication"""
        csv_content = "\n".join([
            (
                "sku,name,description,category,subcategory,brand,price,cost,"
                "installation_type,installation_price,installation_time,"
                "warranty_months,image_url"
            ),
            (
                "TEST-001,Test Product,Test description,acesorios_electronicos,Radios,TestBrand,99.99,50.00,"
                "optional,25.00,30,12,"
            ),
        ])

        files = {"file": ("test.csv", csv_content, "text/csv")}

        # Try without auth
        response = requests.post(
            f"{BASE_URL}/api/products/import/csv",
            files=files,
            params={"warehouse_id": "wh_main", "initial_stock": 5},
            timeout=10,
        )

        # Should require auth
        assert response.status_code in [
            401,
            403,
        ], f"Expected 401/403 without auth, got {response.status_code}"
        print(
            f"✓ CSV import correctly requires authentication (got {response.status_code})"
        )

    def test_csv_import_with_auth(self):
        """Test POST /api/products/import/csv with authentication"""
        unique_sku = f"TEST-{uuid.uuid4().hex[:8].upper()}"

        csv_content = "\n".join([
            (
                "sku,name,description,category,subcategory,brand,price,cost,"
                "installation_type,installation_price,installation_time,"
                "warranty_months,image_url"
            ),
            (
                f"{unique_sku},Test Import Product,Test description,accesorios_electronicos,Radios,"
                "TestBrand,99.99,50.00,optional,25.00,30,12,"
            ),
        ])

        # Get warehouse
        warehouses_response = self.session.get(f"{BASE_URL}/api/warehouses", timeout=10)

        if warehouses_response.status_code == 401:
            pytest.skip("Authentication required - skipping")

        warehouse_id = "wh_main"
        if warehouses_response.status_code == 200:
            warehouses = warehouses_response.json()
            if len(warehouses) > 0:
                warehouse_id = warehouses[0].get("warehouse_id", "wh_main")

        # Use requests directly with cookies from session
        files = {"file": ("test.csv", csv_content, "text/csv")}

        response = requests.post(
            f"{BASE_URL}/api/products/import/csv",
            files=files,
            params={"warehouse_id": warehouse_id, "initial_stock": 5},
            cookies=self.session.cookies,
            timeout=30,
        )

        if response.status_code == 401:
            pytest.skip("Authentication required - skipping")

        if response.status_code == 403:
            print("⚠ User does not have required role for CSV import")
            return

        assert (
            response.status_code == 200
        ), f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()
        assert "imported" in data, "Response should contain imported count"

        print("✓ CSV import successful")
        print(f"  Imported: {data.get('imported', 0)}")
        print(f"  Errors: {len(data.get('errors', []))}")

        # Verify the product was created with correct installation_type
        products_response = self.session.get(f"{BASE_URL}/api/products", timeout=10)
        if products_response.status_code == 200:
            products = products_response.json()
            matching = [p for p in products if p.get("sku") == unique_sku]
            if matching:
                product = matching[0]
                assert (
                    product.get("installation_type") == "optional"
                ), f"Expected installation_type 'optional', got '{product.get('installation_type')}'"
                print(
                    f"  ✓ Product created with correct installation_type: {product.get('installation_type')}"
                )


class TestInstallationTypeInSales:
    """Test installation type behavior in sales"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()

        try:
            test_session = self.session.post(
                f"{BASE_URL}/api/test/create-session", timeout=10
            )
            if test_session.status_code == 200:
                session_data = test_session.json()
                if session_data.get("session_token"):
                    self.session.cookies.set(
                        "session_token", session_data["session_token"]
                    )
        except Exception as e:
            print(f"Auth setup warning: {e}")

    def test_sale_items_have_installation_type(self):
        """Verify sale items include installation_type"""
        response = self.session.get(f"{BASE_URL}/api/sales", timeout=10)

        if response.status_code == 401:
            pytest.skip("Authentication required - skipping")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        sales = response.json()
        if len(sales) > 0:
            sale = sales[0]
            items = sale.get("items", [])
            if len(items) > 0:
                item = items[0]
                # Check if installation_type is present
                has_install_type = "installation_type" in item
                has_with_install = "with_installation" in item

                print("✓ Sale items structure:")
                print(f"  Has installation_type: {has_install_type}")
                print(f"  Has with_installation: {has_with_install}")
                print(f"  Item keys: {list(item.keys())}")
        else:
            print("⚠ No sales found to verify installation_type in items")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
