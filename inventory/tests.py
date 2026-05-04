from django.test import TestCase
from django.urls import reverse

from .models import Product, StockMovement


class InventoryViewsTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name="USB Keyboard",
            sku="KB-001",
            product_type=Product.ProductType.HARDWARE,
            quantity=10,
            purchase_price="20.00",
            unit_price="25.50",
            reorder_level=3,
        )
        self.other_product = Product.objects.create(
            name="Canned Tuna",
            sku="CG-001",
            product_type=Product.ProductType.CANNED_GOODS,
            quantity=8,
            purchase_price="30.00",
            unit_price="39.00",
            reorder_level=2,
        )

    def test_dashboard_loads(self):
        response = self.client.get(reverse("inventory:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Expected Profit")

    def test_stock_in_increases_quantity(self):
        response = self.client.post(
            reverse("inventory:stock-adjust", kwargs={"pk": self.product.pk}),
            {"movement_type": "IN", "quantity": 5, "note": "New delivery"},
            follow=True,
        )
        self.product.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.product.quantity, 15)

    def test_stock_out_cannot_exceed_quantity(self):
        response = self.client.post(
            reverse("inventory:stock-adjust", kwargs={"pk": self.product.pk}),
            {"movement_type": "OUT", "quantity": 20, "note": "Bad request"},
        )
        self.product.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cannot stock out more than available quantity.")
        self.assertEqual(self.product.quantity, 10)

    def test_profit_per_unit_calculation(self):
        self.assertEqual(str(self.product.profit_per_unit), "5.50")

    def test_product_list_filters_by_type(self):
        response = self.client.get(reverse("inventory:product-list"), {"type": Product.ProductType.HARDWARE})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "USB Keyboard")
        self.assertNotContains(response, "Canned Tuna")

    def test_reports_page_loads(self):
        response = self.client.get(reverse("inventory:reports"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Export Inventory to Excel")
        self.assertContains(response, "Print Stock Report")

    def test_inventory_export_downloads_excel_file(self):
        response = self.client.get(reverse("inventory:inventory-export"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/vnd.ms-excel")
        self.assertIn("inventory-report.xls", response["Content-Disposition"])
        self.assertContains(response, "USB Keyboard")

    def test_stock_report_loads(self):
        StockMovement.objects.create(
            product=self.product,
            movement_type=StockMovement.MovementType.STOCK_IN,
            quantity=5,
            note="New delivery",
        )
        response = self.client.get(reverse("inventory:stock-report"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "USB Keyboard")
        self.assertContains(response, "New delivery")
