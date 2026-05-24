import json
from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse

from .forms import UserRegistrationForm
from .models import Chat, ChatReadState, Notification, Product, StockMovement, Transaction, TransactionItem, UserProfile, UserRegistration


class InventoryViewsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="staffuser",
            password="StaffPassword123!",
            is_staff=True,
            is_superuser=True,
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
        self.assertContains(response, "similar-products-scroll")
        self.assertContains(response, "pos-search-qty")
        self.assertContains(response, "addProductFromRow")
        self.assertContains(response, "<th style=\"text-align: center; padding: var(--spacing-md);\">Qty</th>", html=False)

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
        self.product.quantity = 2
        self.product.save()
        StockMovement.objects.create(
            product=self.product,
            movement_type=StockMovement.MovementType.STOCK_IN,
            quantity=5,
            note="New delivery",
        )
        response = self.client.get(reverse("inventory:stock-report"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Stock Priority Report")
        self.assertContains(response, "Low Stock Items")
        self.assertContains(response, "Top Products To Buy")
        self.assertContains(response, "Least Bought/Sold Products")
        self.assertContains(response, "USB Keyboard")
        self.assertNotContains(response, "New delivery")

    def test_stock_export_downloads_priority_report(self):
        self.product.quantity = 2
        self.product.save()
        StockMovement.objects.create(
            product=self.product,
            movement_type=StockMovement.MovementType.STOCK_IN,
            quantity=5,
            note="New delivery",
        )

        response = self.client.get(reverse("inventory:stock-export"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/vnd.ms-excel")
        self.assertIn("stock-report.xls", response["Content-Disposition"])
        self.assertContains(response, "Stock Priority Report")
        self.assertContains(response, "Recommended Buy Qty")
        self.assertContains(response, "Units Bought")
        self.assertContains(response, "Buy urgently")
        self.assertNotContains(response, "New delivery")

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
        self.staff.profile.address = "123 Main Street"
        self.staff.profile.birthday = date(2000, 1, 1)
        self.staff.profile.save()
        self.client.force_login(self.admin)

    def test_staff_list_has_manage_and_remove_buttons(self):
        response = self.client.get(reverse("inventory:staff-list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Manage")
        self.assertContains(response, "Remove")
        self.assertContains(response, reverse("inventory:staff-edit", kwargs={"staff_id": self.staff.id}))
        self.assertContains(response, reverse("inventory:staff-remove", kwargs={"staff_id": self.staff.id}))
        self.assertContains(response, "123 Main Street")
        self.assertContains(response, "Jan 01, 2000")
        self.assertContains(response, str(self.staff.profile.age))

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

    def test_admin_can_edit_staff_account_and_profile(self):
        new_password = "UpdatedCashierPassword123!"

        response = self.client.post(
            reverse("inventory:staff-edit", kwargs={"staff_id": self.staff.id}),
            {
                "username": "frontcashier",
                "first_name": "Front",
                "last_name": "Counter",
                "address": "456 Market Road",
                "birthday": "1995-05-24",
                "new_password": new_password,
                "confirm_password": new_password,
            },
        )

        self.staff.refresh_from_db()
        self.staff.profile.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.staff.username, "frontcashier")
        self.assertEqual(self.staff.first_name, "Front")
        self.assertEqual(self.staff.last_name, "Counter")
        self.assertEqual(self.staff.profile.address, "456 Market Road")
        self.assertEqual(self.staff.profile.birthday, date(1995, 5, 24))
        self.assertTrue(self.staff.check_password(new_password))

    def test_admin_can_remove_staff_member(self):
        response = self.client.post(reverse("inventory:staff-remove", kwargs={"staff_id": self.staff.id}))

        self.assertEqual(response.status_code, 302)
        self.assertFalse(User.objects.filter(id=self.staff.id).exists())


class RoleAccessTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name="Role Test Item",
            sku="ROLE-001",
            product_type=Product.ProductType.OTHER,
            quantity=20,
            purchase_price="10.00",
            unit_price="20.00",
            reorder_level=5,
        )
        self.cashier = User.objects.create_user(
            username="rolecashier",
            password="CashierPassword123!",
            is_staff=True,
        )
        self.cashier.profile.staff_role = UserProfile.StaffRole.CASHIER
        self.cashier.profile.save()
        self.inventory_staff = User.objects.create_user(
            username="rolestock",
            password="InventoryPassword123!",
            is_staff=True,
        )
        self.inventory_staff.profile.staff_role = UserProfile.StaffRole.INVENTORY
        self.inventory_staff.profile.save()

    def test_cashier_access_is_limited_to_pos_and_sales_history(self):
        self.client.force_login(self.cashier)

        self.assertEqual(self.client.get(reverse("inventory:pos")).status_code, 200)
        self.assertEqual(self.client.get(reverse("inventory:sales-history")).status_code, 200)
        self.assertEqual(self.client.get(reverse("inventory:product-list")).status_code, 302)
        self.assertEqual(self.client.get(reverse("inventory:reports")).status_code, 302)
        self.assertEqual(self.client.get(reverse("inventory:settings")).status_code, 302)
        self.assertEqual(self.client.get(reverse("inventory:staff-list")).status_code, 302)

    def test_inventory_staff_can_update_stock_without_financial_analytics_or_pos(self):
        self.client.force_login(self.inventory_staff)

        response = self.client.get(reverse("inventory:product-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Product Inventory")
        self.assertNotContains(response, "Profit/Unit")

        response = self.client.post(
            reverse("inventory:stock-adjust", kwargs={"pk": self.product.pk}),
            {"movement_type": StockMovement.MovementType.STOCK_IN, "quantity": 5, "note": "Supplier delivery"},
        )
        self.product.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.product.quantity, 25)

        response = self.client.get(reverse("inventory:stock-report"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Stock Priority Report")
        self.assertNotContains(response, "Selling Price")

        self.assertEqual(self.client.get(reverse("inventory:pos")).status_code, 302)
        self.assertEqual(self.client.get(reverse("inventory:reports")).status_code, 302)
        self.assertEqual(self.client.get(reverse("inventory:sales-history")).status_code, 302)

    def test_cashier_discount_is_limited(self):
        self.client.force_login(self.cashier)
        session = self.client.session
        session["cart"] = {
            str(self.product.id): {
                "product_id": self.product.id,
                "name": self.product.name,
                "sku": self.product.sku,
                "price": 100.0,
                "quantity": 1,
            }
        }
        session.save()

        response = self.client.post(reverse("inventory:pos-apply-discount"), {"discount": "15.00"})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["success"])
        self.assertIn("Cashier discount limit", response.json()["message"])

        response = self.client.post(reverse("inventory:pos-apply-discount"), {"discount": "10.00"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])


class ChatWidgetRoleTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name="Chat Test Item",
            sku="CHAT-001",
            product_type=Product.ProductType.OTHER,
            quantity=10,
            purchase_price="8.00",
            unit_price="12.00",
            reorder_level=2,
        )
        self.ellar_admin = User.objects.create_user(
            username="EllarMiniMart",
            password="AdminPassword123!",
            is_staff=True,
        )
        self.cashier = User.objects.create_user(
            username="chatcashier",
            password="CashierPassword123!",
            is_staff=True,
        )
        self.cashier.profile.staff_role = UserProfile.StaffRole.CASHIER
        self.cashier.profile.save()
        self.inventory_staff = User.objects.create_user(
            username="chatinventory",
            password="InventoryPassword123!",
            is_staff=True,
        )
        self.inventory_staff.profile.staff_role = UserProfile.StaffRole.INVENTORY
        self.inventory_staff.profile.save()

    def test_floating_chat_widget_renders_for_all_app_roles(self):
        pages = [
            (self.ellar_admin, reverse("inventory:dashboard")),
            (self.cashier, reverse("inventory:pos")),
            (self.inventory_staff, reverse("inventory:product-list")),
        ]

        for user, url in pages:
            with self.subTest(username=user.username):
                self.client.force_login(user)
                response = self.client.get(url)

                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'id="floatingChatBtn"')
                self.assertContains(response, 'class="chat-item group-chat-item"')
                self.assertContains(response, "groupChatItem.addEventListener('click'")

    def test_admin_delete_page_uses_chat_enabled_layout(self):
        self.client.force_login(self.ellar_admin)

        response = self.client.get(reverse("inventory:product-delete", kwargs={"pk": self.product.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="floatingChatBtn"')

    def test_group_chat_api_includes_all_staff_roles(self):
        for user in [self.ellar_admin, self.cashier, self.inventory_staff]:
            with self.subTest(username=user.username):
                self.client.force_login(user)
                response = self.client.get(
                    reverse("inventory:api-group-chat"),
                    HTTP_X_REQUESTED_WITH="XMLHttpRequest",
                )

                self.assertEqual(response.status_code, 200)
                data = response.json()
                self.assertTrue(data["success"])

        chat = Chat.objects.get(name="All Employees", chat_type=Chat.ChatType.GROUP)
        self.assertTrue(chat.participants.filter(id=self.ellar_admin.id).exists())
        self.assertTrue(chat.participants.filter(id=self.cashier.id).exists())
        self.assertTrue(chat.participants.filter(id=self.inventory_staff.id).exists())

    def test_group_chat_api_messages_are_available_to_staff_and_admin(self):
        self.client.force_login(self.cashier)
        response = self.client.get(
            reverse("inventory:api-group-chat"),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        chat_id = response.json()["chat_id"]

        response = self.client.post(
            reverse("inventory:api-send-message", kwargs={"chat_id": chat_id}),
            data=json.dumps({"content": "Hello everyone"}),
            content_type="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])

        self.client.force_login(self.ellar_admin)
        response = self.client.get(
            reverse("inventory:api-messages", kwargs={"chat_id": chat_id}),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        self.assertEqual(response.json()["messages"][0]["content"], "Hello everyone")

    def test_unread_counts_are_tracked_per_current_user(self):
        self.client.force_login(self.cashier)
        response = self.client.get(
            reverse("inventory:api-group-chat"),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        chat_id = response.json()["chat_id"]

        response = self.client.post(
            reverse("inventory:api-send-message", kwargs={"chat_id": chat_id}),
            data=json.dumps({"content": "Unread for everyone else"}),
            content_type="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)

        self.client.force_login(self.ellar_admin)
        response = self.client.get(reverse("inventory:api-chats"), HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        admin_data = response.json()
        self.assertEqual(admin_data["unread_total"], 1)
        self.assertEqual(admin_data["chats"][0]["unread_count"], 1)

        response = self.client.get(
            reverse("inventory:api-messages", kwargs={"chat_id": chat_id}),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(ChatReadState.objects.filter(chat_id=chat_id, user=self.ellar_admin).exists())

        response = self.client.get(reverse("inventory:api-chats"), HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.json()["unread_total"], 0)

        self.client.force_login(self.inventory_staff)
        response = self.client.get(reverse("inventory:api-chats"), HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        inventory_data = response.json()
        self.assertEqual(inventory_data["unread_total"], 1)
        self.assertEqual(inventory_data["chats"][0]["unread_count"], 1)

    def test_employee_can_direct_message_ellar_admin(self):
        self.client.force_login(self.cashier)

        response = self.client.get(
            reverse("inventory:api-direct-chat", kwargs={"user_id": self.ellar_admin.id}),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data["success"])

        chat = Chat.objects.get(id=data["chat_id"])
        self.assertTrue(chat.participants.filter(id=self.cashier.id).exists())
        self.assertTrue(chat.participants.filter(id=self.ellar_admin.id).exists())

        response = self.client.post(
            reverse("inventory:api-send-message", kwargs={"chat_id": chat.id}),
            data=json.dumps({"content": "Hi Ellar"}),
            content_type="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])

        self.client.force_login(self.ellar_admin)
        response = self.client.get(
            reverse("inventory:api-messages", kwargs={"chat_id": chat.id}),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["messages"][0]["content"], "Hi Ellar")

    def test_employee_can_delete_direct_chat_but_not_group_chat(self):
        self.client.force_login(self.cashier)

        response = self.client.get(
            reverse("inventory:api-direct-chat", kwargs={"user_id": self.ellar_admin.id}),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        direct_chat_id = response.json()["chat_id"]

        response = self.client.post(
            reverse("inventory:api-delete-chat", kwargs={"chat_id": direct_chat_id}),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        self.assertFalse(Chat.objects.filter(id=direct_chat_id).exists())

        response = self.client.get(
            reverse("inventory:api-group-chat"),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        group_chat_id = response.json()["chat_id"]

        response = self.client.post(
            reverse("inventory:api-delete-chat", kwargs={"chat_id": group_chat_id}),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["success"])
        self.assertTrue(Chat.objects.filter(id=group_chat_id).exists())

    def test_chat_selection_opens_messages_without_menu_tab(self):
        self.client.force_login(self.ellar_admin)
        response = self.client.get(reverse("inventory:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Show messages without exposing a separate Messages tab")
        self.assertNotContains(response, 'data-tab="chat-view"')
        self.assertNotContains(response, "messagesTab.click()")
        self.assertContains(response, 'id="chatUnreadBadge"')
        self.assertContains(response, "updateChatUnreadBadge(data.unread_total)")
        self.assertContains(response, "renderUnreadIndicator(chat.unread_count)")
        self.assertContains(response, "deleteChat(chat.id)")
        self.assertContains(response, "/delete/`")
        self.assertNotContains(response, "chatTabs[1].click()")
        self.assertNotContains(response, "chatTabs[0].click()")


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
        self.assertContains(response, reverse("inventory:mark-all-notifications-read"))
        self.assertContains(response, 'id="markAllNotificationsBtn"')

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

    def test_superuser_can_mark_all_notifications_read(self):
        Notification.objects.create(
            type=Notification.NotificationType.LOW_STOCK,
            title="Low Stock",
            message="An item is low.",
            created_by=self.staff,
        )

        response = self.client.post(
            reverse("inventory:mark-all-notifications-read"),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        self.assertEqual(response.json()["unread_count"], 0)
        self.assertEqual(Notification.objects.filter(is_read=False).count(), 0)

        response = self.client.get(reverse("inventory:api-notifications"))
        self.assertEqual(response.json()["unread_count"], 0)

    def test_notifications_page_loads_for_superuser_with_any_username(self):
        response = self.client.get(reverse("inventory:notifications"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "System Notifications")
        self.assertContains(response, "Mark all as read")
        self.assertContains(response, reverse("inventory:mark-all-notifications-read"))
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

        self.assertIn("staff_role", form.fields)
        self.assertNotIn("branch", form.fields)

        response = self.client.get(reverse("inventory:register"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Staff Role")
        self.assertNotContains(response, "Branch")
        self.assertNotContains(response, 'name="branch"')

    def test_staff_registration_saves_with_default_branch_and_role(self):
        response = self.client.post(
            reverse("inventory:register"),
            {
                "username": "newcashier",
                "email": "newcashier@example.com",
                "first_name": "New",
                "last_name": "Cashier",
                "staff_role": UserRegistration.StaffRole.CASHIER,
                "phone": "09170000000",
                "location": "Front counter",
                "password": "StaffPassword123!",
                "confirm_password": "StaffPassword123!",
            },
        )

        self.assertEqual(response.status_code, 302)
        registration = UserRegistration.objects.get(username="newcashier")
        self.assertEqual(registration.branch, "main")
        self.assertEqual(registration.staff_role, UserRegistration.StaffRole.CASHIER)

    def test_approval_assigns_selected_staff_role(self):
        admin = User.objects.create_user(
            username="EllarMiniMart",
            password="AdminPassword123!",
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_login(admin)
        registration = UserRegistration.objects.create(
            username="stockstaff",
            email="stockstaff@example.com",
            first_name="Stock",
            last_name="Staff",
            staff_role=UserRegistration.StaffRole.INVENTORY,
            location="Back storage room",
            password="hashed-password",
        )

        response = self.client.post(reverse("inventory:approve-user", kwargs={"registration_id": registration.id}))

        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username="stockstaff")
        self.assertEqual(user.profile.staff_role, UserProfile.StaffRole.INVENTORY)
        self.assertEqual(user.profile.address, "Back storage room")
