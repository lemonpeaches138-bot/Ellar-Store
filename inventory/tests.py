import json
from decimal import Decimal

from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse

from .forms import UserRegistrationForm
from .models import Notification, Product, StockMovement, Transaction, TransactionItem, UserRegistration


class InventoryViewsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="staffuser",
            password="StaffPassword123!",
            is_staff=True,
        )
        self.client.force_login(self.user)
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

    def test_stock_adjust_ajax_returns_updated_quantity(self):
        response = self.client.post(
            reverse("inventory:stock-adjust", kwargs={"pk": self.product.pk}),
            {"movement_type": "IN", "quantity": 4, "note": "Modal update"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.product.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["quantity"], 14)
        self.assertEqual(self.product.quantity, 14)

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
        self.assertContains(response, "Print Report")

    def test_reports_analytics_use_saved_system_data(self):
        transaction = Transaction.objects.create(
            transaction_id="TXNREPORT001",
            subtotal="76.50",
            discount="5.00",
            total="71.50",
            cash_received="100.00",
            change="28.50",
        )
        TransactionItem.objects.create(
            transaction=transaction,
            product=self.product,
            quantity=3,
            unit_price="25.50",
            subtotal="76.50",
        )
        StockMovement.objects.create(
            product=self.product,
            movement_type=StockMovement.MovementType.STOCK_OUT,
            quantity=3,
            note="POS sale",
        )

        response = self.client.get(reverse("inventory:reports"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_units_sold"], 3)
        self.assertEqual(response.context["total_revenue"], Decimal("71.50"))
        self.assertEqual(response.context["gross_revenue"], Decimal("76.50"))
        self.assertEqual(response.context["total_discount"], Decimal("5.00"))
        self.assertEqual(response.context["stock_out_units"], 3)
        self.assertEqual(response.context["top_products"][0].id, self.product.id)
        self.assertEqual(response.context["top_products"][0].sales_units, 3)
        self.assertEqual(response.context["top_products"][0].sales_revenue, Decimal("76.50"))
        self.assertIn(71.5, response.context["sales_trends"]["week"]["data"])
        self.assertContains(response, "Sales Revenue Trend")
        self.assertContains(response, "Product Count by Category")
        self.assertNotContains(response, "[12000, 19000, 15000")

    def test_pos_page_loads(self):
        response = self.client.get(reverse("inventory:pos"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Point of Sale")
        self.assertContains(response, reverse("inventory:pos-checkout"))

    def test_settings_page_loads(self):
        response = self.client.get(reverse("inventory:settings"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Theme Mode")
        self.assertContains(response, reverse("inventory:api-update-theme"))

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

    def test_theme_api_update_persists_mode_and_color(self):
        self.user.profile.dark_mode = True
        self.user.profile.primary_color = "pink"
        self.user.profile.save()

        response = self.client.post(
            reverse("inventory:api-update-theme"),
            data=json.dumps({"dark_mode": False, "primary_color": "green"}),
            content_type="application/json",
        )

        self.user.profile.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.user.profile.dark_mode)
        self.assertEqual(self.user.profile.primary_color, "green")
        self.assertEqual(response.json()["config"]["hex"], "#10b981")

    def test_theme_api_rejects_invalid_primary_color(self):
        response = self.client.post(
            reverse("inventory:api-update-theme"),
            data=json.dumps({"primary_color": "neon"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["success"])

    def test_base_template_uses_saved_theme_before_javascript_runs(self):
        self.user.profile.dark_mode = False
        self.user.profile.primary_color = "blue"
        self.user.profile.save()

        response = self.client.get(reverse("inventory:dashboard"))
        self.assertContains(response, '<body class="">')
        self.assertContains(response, "--primary-color: #3b82f6;")

        self.user.profile.dark_mode = True
        self.user.profile.save()

        response = self.client.get(reverse("inventory:dashboard"))
        self.assertContains(response, '<body class="dark-mode">')

    def test_receipt_uses_saved_primary_color(self):
        self.user.profile.primary_color = "pink"
        self.user.profile.save()
        transaction = Transaction.objects.create(
            transaction_id="TXNTESTPINK",
            subtotal="100.00",
            discount="0.00",
            total="100.00",
            cash_received="100.00",
            change="0.00",
        )

        response = self.client.get(reverse("inventory:pos-receipt", kwargs={"transaction_id": transaction.transaction_id}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["X-Frame-Options"], "SAMEORIGIN")
        self.assertContains(response, "--primary-color: #ec4899;")
        self.assertContains(response, "background: var(--primary-gradient);")
        self.assertNotContains(response, "#667eea")

    def test_pos_search_accepts_product_id_from_browser_cards(self):
        response = self.client.get(reverse("inventory:pos-search"), {"q": str(self.product.id)})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        self.assertEqual(response.json()["product"]["id"], self.product.id)


class StaffManagementTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="EllarMiniMart",
            password="AdminPassword123!",
            is_staff=True,
            is_superuser=True,
        )
        self.staff = User.objects.create_user(
            username="cashier",
            password="OldPassword123!",
            email="cashier@example.com",
            first_name="Store",
            last_name="Cashier",
            is_staff=True,
        )
        self.client.force_login(self.admin)

    def test_staff_list_has_manage_and_remove_buttons(self):
        response = self.client.get(reverse("inventory:staff-list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Manage")
        self.assertContains(response, "Remove")
        self.assertContains(response, reverse("inventory:staff-set-password", kwargs={"staff_id": self.staff.id}))
        self.assertContains(response, reverse("inventory:staff-remove", kwargs={"staff_id": self.staff.id}))

    def test_admin_can_reset_staff_password(self):
        new_password = "NewCashierPassword123!"

        response = self.client.post(
            reverse("inventory:staff-set-password", kwargs={"staff_id": self.staff.id}),
            {
                "new_password": new_password,
                "confirm_password": new_password,
            },
        )

        self.staff.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.staff.check_password(new_password))

    def test_admin_can_remove_staff_member(self):
        response = self.client.post(reverse("inventory:staff-remove", kwargs={"staff_id": self.staff.id}))

        self.assertEqual(response.status_code, 302)
        self.assertFalse(User.objects.filter(id=self.staff.id).exists())


class NotificationAdminTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="renderadmin",
            password="AdminPassword123!",
            is_staff=True,
            is_superuser=True,
        )
        self.staff = User.objects.create_user(
            username="cashier",
            password="CashierPassword123!",
            is_staff=True,
        )
        self.notification = Notification.objects.create(
            type=Notification.NotificationType.SALE,
            title="Sale Completed",
            message="A sale was completed.",
            created_by=self.staff,
        )
        self.client.force_login(self.admin)

    def test_superuser_with_any_username_sees_notification_ui(self):
        response = self.client.get(reverse("inventory:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="notificationBtn"')
        self.assertContains(response, reverse("inventory:api-notifications"))

    def test_superuser_with_any_username_can_load_and_mark_notifications(self):
        response = self.client.get(reverse("inventory:api-notifications"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["unread_count"], 1)

        response = self.client.post(
            reverse("inventory:mark-notification-read", kwargs={"notification_id": self.notification.id}),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.notification.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        self.assertTrue(self.notification.is_read)

    def test_notifications_page_loads_for_superuser_with_any_username(self):
        response = self.client.get(reverse("inventory:notifications"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "System Notifications")
        self.assertContains(
            response,
            reverse("inventory:mark-notification-read", kwargs={"notification_id": self.notification.id}),
        )

    def test_login_creates_notification_without_legacy_admin_username(self):
        self.client.logout()

        response = self.client.post(
            reverse("inventory:login"),
            {"username": self.staff.username, "password": "CashierPassword123!"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Notification.objects.filter(title=f"Staff Login: {self.staff.username}").exists())


class StaffRegistrationTests(TestCase):
    def test_staff_registration_form_does_not_show_branch(self):
        form = UserRegistrationForm()

        self.assertNotIn("branch", form.fields)

        response = self.client.get(reverse("inventory:register"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Branch")
        self.assertNotContains(response, 'name="branch"')

    def test_staff_registration_saves_with_default_branch(self):
        response = self.client.post(
            reverse("inventory:register"),
            {
                "username": "newcashier",
                "email": "newcashier@example.com",
                "first_name": "New",
                "last_name": "Cashier",
                "phone": "09170000000",
                "location": "Front counter",
                "password": "StaffPassword123!",
                "confirm_password": "StaffPassword123!",
            },
        )

        self.assertEqual(response.status_code, 302)
        registration = UserRegistration.objects.get(username="newcashier")
        self.assertEqual(registration.branch, "main")
