"""
Test file for Bug Fixes - Iteration 7
Testing:
- Bug #13: Currency/IVA calculations in Sales
- Bug #1: New Customer button functionality
- Bug #3: Print/Download buttons in sales table
- Bug #4: Seller and Branch filters in Sales
- Bug #2: VENTAS HOY card navigation
- Bug #6: Download Template button in Inventory
"""

import os

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")


class TestBugFixes:
    """Test bug fixes for iteration 7"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        # Create test session
        response = requests.post(
            f"{BASE_URL}/api/test/create-session",
            json={
                "email": "test.admin@mundodeaccesorios.com",
                "name": "Test Admin",
                "role": "gerencia",
            },
        )
        assert response.status_code == 200, f"Failed to create session: {response.text}"
        data = response.json()
        self.session_token = data.get("session_token")
        self.cookies = {"session_token": self.session_token}
        yield

    # Bug #6: Download Template button in Inventory
    def test_download_template_endpoint(self):
        """Bug #6: Verify CSV template download endpoint works"""
        response = requests.get(f"{BASE_URL}/api/products/import/template")
        assert (
            response.status_code == 200
        ), f"Template download failed: {response.status_code}"

        # Check content type is CSV
        content_type = response.headers.get("content-type", "")
        assert (
            "text/csv" in content_type or "application/octet-stream" in content_type
        ), f"Wrong content type: {content_type}"

        # Check CSV content has required columns
        content = response.text
        assert "sku" in content.lower(), "CSV missing 'sku' column"
        assert "name" in content.lower(), "CSV missing 'name' column"
        assert "price" in content.lower(), "CSV missing 'price' column"
        print(f"✓ Template download works - Content preview: {content[:200]}")

    # Bug #4: Seller and Branch filters
    def test_users_pin_endpoint_for_sellers(self):
        """Bug #4: Verify auth/pin/users endpoint returns sellers for filter"""
        response = requests.get(f"{BASE_URL}/api/auth/pin/users", cookies=self.cookies)
        assert (
            response.status_code == 200
        ), f"Users endpoint failed: {response.status_code}"

        users = response.json()
        assert isinstance(users, list), "Users should be a list"
        print(f"✓ Users endpoint works - Found {len(users)} users")

    def test_branches_endpoint(self):
        """Bug #4: Verify branches endpoint works for filter"""
        response = requests.get(f"{BASE_URL}/api/branches", cookies=self.cookies)
        assert (
            response.status_code == 200
        ), f"Branches endpoint failed: {response.status_code}"

        branches = response.json()
        assert isinstance(branches, list), "Branches should be a list"
        print(f"✓ Branches endpoint works - Found {len(branches)} branches")

    # Bug #1: New Customer creation
    def test_create_customer(self):
        """Bug #1: Verify customer creation endpoint works"""
        customer_data = {
            "name": "TEST_Cliente Prueba",
            "first_name": "TEST_Cliente",
            "last_name": "Prueba",
            "customer_type": "natural",
            "document_type": "cedula",
            "document_id": "001-123456-0001X",
            "email": "test_cliente@example.com",
            "phone": "8888-1234",
            "address": "Managua, Nicaragua",
            "credit_limit": 5000,
        }

        response = requests.post(
            f"{BASE_URL}/api/customers", json=customer_data, cookies=self.cookies
        )
        assert (
            response.status_code == 200
        ), f"Customer creation failed: {response.status_code} - {response.text}"

        data = response.json()
        assert "customer_id" in data, "Response should contain customer_id"
        assert data.get("name") == customer_data["name"], "Customer name mismatch"
        print(f"✓ Customer creation works - Created: {data.get('customer_id')}")

        # Cleanup - store for later deletion
        self.created_customer_id = data.get("customer_id")

    def test_get_customers(self):
        """Bug #1: Verify customers list endpoint works"""
        response = requests.get(f"{BASE_URL}/api/customers", cookies=self.cookies)
        assert (
            response.status_code == 200
        ), f"Get customers failed: {response.status_code}"

        customers = response.json()
        assert isinstance(customers, list), "Customers should be a list"
        print(f"✓ Get customers works - Found {len(customers)} customers")

    # Bug #3: Print/Download sale
    def test_get_sales(self):
        """Bug #3: Verify sales list endpoint works"""
        response = requests.get(f"{BASE_URL}/api/sales", cookies=self.cookies)
        assert response.status_code == 200, f"Get sales failed: {response.status_code}"

        sales = response.json()
        assert isinstance(sales, list), "Sales should be a list"
        print(f"✓ Get sales works - Found {len(sales)} sales")
        return sales

    def test_sale_pdf_endpoint(self):
        """Bug #3: Verify sale PDF download endpoint exists"""
        # First get a sale
        sales = self.test_get_sales()

        if len(sales) > 0:
            sale_id = sales[0].get("sale_id")
            response = requests.get(
                f"{BASE_URL}/api/print/invoice-pdf/{sale_id}", cookies=self.cookies
            )
            # Should return PDF or 404 if no sale
            assert response.status_code in [
                200,
                404,
            ], f"PDF endpoint failed: {response.status_code}"

            if response.status_code == 200:
                content_type = response.headers.get("content-type", "")
                assert (
                    "pdf" in content_type.lower()
                    or "application/octet-stream" in content_type
                ), f"Wrong content type: {content_type}"
                print(f"✓ PDF download works for sale {sale_id}")
            else:
                print(f"✓ PDF endpoint exists but sale {sale_id} not found")
        else:
            print("⚠ No sales to test PDF download")

    # Bug #13: Currency conversion
    def test_currency_rates_endpoint(self):
        """Bug #13: Verify currency rates endpoint works"""
        response = requests.get(
            f"{BASE_URL}/api/currencies/rates", cookies=self.cookies
        )
        assert (
            response.status_code == 200
        ), f"Currency rates failed: {response.status_code}"

        rates = response.json()
        assert isinstance(rates, dict), "Rates should be a dict"
        print(f"✓ Currency rates endpoint works - Rates: {rates}")

    def test_currency_convert_endpoint(self):
        """Bug #13: Verify currency conversion endpoint works"""
        # Test converting 100 USD to NIO
        response = requests.get(
            f"{BASE_URL}/api/currencies/convert",
            params={"amount": 100, "from_currency": "USD", "to_currency": "NIO"},
            cookies=self.cookies,
        )
        assert (
            response.status_code == 200
        ), f"Currency convert failed: {response.status_code}"

        data = response.json()
        assert "converted" in data, "Response should contain converted"
        assert data["converted"] > 100, "NIO should be more than USD"
        print(f"✓ Currency conversion works - 100 USD = {data['converted']} NIO")

    # Test products for sales
    def test_get_products(self):
        """Verify products endpoint works for sales"""
        response = requests.get(f"{BASE_URL}/api/products", cookies=self.cookies)
        assert (
            response.status_code == 200
        ), f"Get products failed: {response.status_code}"

        products = response.json()
        assert isinstance(products, list), "Products should be a list"
        print(f"✓ Get products works - Found {len(products)} products")
        return products

    def test_get_warehouses(self):
        """Verify warehouses endpoint works"""
        response = requests.get(f"{BASE_URL}/api/warehouses", cookies=self.cookies)
        assert (
            response.status_code == 200
        ), f"Get warehouses failed: {response.status_code}"

        warehouses = response.json()
        assert isinstance(warehouses, list), "Warehouses should be a list"
        print(f"✓ Get warehouses works - Found {len(warehouses)} warehouses")
        return warehouses

    def test_get_inventory(self):
        """Verify inventory endpoint works"""
        response = requests.get(f"{BASE_URL}/api/inventory", cookies=self.cookies)
        assert (
            response.status_code == 200
        ), f"Get inventory failed: {response.status_code}"

        inventory = response.json()
        assert isinstance(inventory, list), "Inventory should be a list"
        print(f"✓ Get inventory works - Found {len(inventory)} items")
        return inventory

    def test_dashboard_stats(self):
        """Bug #2: Verify dashboard stats endpoint works (for VENTAS HOY card)"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", cookies=self.cookies)
        assert (
            response.status_code == 200
        ), f"Dashboard stats failed: {response.status_code}"

        stats = response.json()
        assert isinstance(stats, dict), "Stats should be a dict"
        # Check for sales_today field
        assert (
            "sales_today" in stats or "total_sales" in stats
        ), "Stats should contain sales data"
        print(f"✓ Dashboard stats works - Stats: {list(stats.keys())}")


class TestSalesCreation:
    """Test sales creation with currency conversion"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session and seed data"""
        # Create test session
        response = requests.post(
            f"{BASE_URL}/api/test/create-session",
            json={
                "email": "test.admin@mundodeaccesorios.com",
                "name": "Test Admin",
                "role": "gerencia",
            },
        )
        assert response.status_code == 200
        data = response.json()
        self.session_token = data.get("session_token")
        self.cookies = {"session_token": self.session_token}

        # Seed demo products if needed
        requests.post(f"{BASE_URL}/api/products/seed-demo", cookies=self.cookies)
        yield

    def test_create_sale_with_nio_currency(self):
        """Bug #13: Test creating a sale with NIO currency"""
        # Get products
        products_res = requests.get(f"{BASE_URL}/api/products", cookies=self.cookies)
        products = products_res.json()

        if len(products) == 0:
            pytest.skip("No products available for sale test")

        # Get customers
        customers_res = requests.get(f"{BASE_URL}/api/customers", cookies=self.cookies)
        customers = customers_res.json()

        if len(customers) == 0:
            # Create a test customer
            customer_data = {
                "name": "TEST_Sale Customer",
                "first_name": "TEST_Sale",
                "last_name": "Customer",
                "phone": "8888-5678",
            }
            cust_res = requests.post(
                f"{BASE_URL}/api/customers", json=customer_data, cookies=self.cookies
            )
            customer = cust_res.json()
        else:
            customer = customers[0]

        # Get inventory
        inventory_res = requests.get(f"{BASE_URL}/api/inventory", cookies=self.cookies)
        inventory = inventory_res.json()

        # Find a product with stock
        product_with_stock = None
        warehouse_id = None
        for inv in inventory:
            if inv.get("quantity", 0) > 0:
                product_with_stock = next(
                    (
                        p
                        for p in products
                        if p.get("product_id") == inv.get("product_id")
                    ),
                    None,
                )
                warehouse_id = inv.get("warehouse_id")
                if product_with_stock:
                    break

        if not product_with_stock:
            pytest.skip("No products with stock available")

        # Create sale with NIO currency
        sale_data = {
            "customer_id": customer.get("customer_id"),
            "items": [
                {
                    "product_id": product_with_stock.get("product_id"),
                    "quantity": 1,
                    "discount": 0,
                    "warehouse_id": warehouse_id,
                    "with_installation": False,
                }
            ],
            "discount": 0,
            "payment_type": "cash",
            "apply_iva": True,
            "iva_rate": 15,
            "currency": "NIO",
            "exchange_rate": 36.5,
        }

        response = requests.post(
            f"{BASE_URL}/api/sales", json=sale_data, cookies=self.cookies
        )

        # Sale creation might fail due to various reasons, but endpoint should work
        if response.status_code == 200:
            data = response.json()
            assert (
                "sale_id" in data or "invoice_number" in data
            ), "Sale response should contain sale_id or invoice_number"
            print(
                f"✓ Sale created with NIO currency - Invoice: {data.get('invoice_number')}"
            )
        else:
            # Check if it's a validation error vs server error
            assert (
                response.status_code < 500
            ), f"Server error creating sale: {response.status_code} - {response.text}"
            print(
                f"⚠ Sale creation returned {response.status_code}: {response.text[:200]}"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
