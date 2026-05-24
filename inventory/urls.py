from django.urls import path

from . import views

app_name = "inventory"

urlpatterns = [
    path("", views.index_redirect, name="index"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register_user, name="register"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("products/", views.product_list, name="product-list"),
    path("products/add/", views.product_create, name="product-add"),
    path("products/<int:pk>/edit/", views.product_update, name="product-edit"),
    path("products/<int:pk>/delete/", views.product_delete, name="product-delete"),
    path("products/<int:pk>/stock/", views.stock_adjust, name="stock-adjust"),
    path("reports/", views.reports, name="reports"),
    path("reports/inventory.xls", views.inventory_export, name="inventory-export"),
    path("reports/stock/", views.stock_report, name="stock-report"),
    path("reports/stock.xls", views.stock_export, name="stock-export"),
    path("admin-profile/", views.admin_profile, name="admin-profile"),
    path("user-approvals/", views.user_approvals, name="user-approvals"),
    path("approve-user/<int:registration_id>/", views.approve_user, name="approve-user"),
    path("reject-user/<int:registration_id>/", views.reject_user, name="reject-user"),
    path("staff-list/", views.staff_list, name="staff-list"),
    path("staff-list/<int:staff_id>/edit/", views.staff_edit, name="staff-edit"),
    path("staff-list/<int:staff_id>/password/", views.staff_set_password, name="staff-set-password"),
    path("staff-list/<int:staff_id>/remove/", views.staff_remove, name="staff-remove"),
    path("notifications/", views.notifications, name="notifications"),
    path("api/notifications/", views.api_notifications, name="api-notifications"),
    path("mark-notification-read/<int:notification_id>/", views.mark_notification_read, name="mark-notification-read"),
    path("mark-all-notifications-read/", views.mark_all_notifications_read, name="mark-all-notifications-read"),
    # POS URLs
    path("pos/", views.pos, name="pos"),
    path("pos/sales/", views.sales_history, name="sales-history"),
    path("pos/search/", views.pos_search_product, name="pos-search"),
    path("pos/products/", views.pos_get_products, name="pos-get-products"),
    path("pos/add-item/", views.pos_add_item, name="pos-add-item"),
    path("pos/remove-item/", views.pos_remove_item, name="pos-remove-item"),
    path("pos/update-quantity/", views.pos_update_quantity, name="pos-update-quantity"),
    path("pos/apply-discount/", views.pos_apply_discount, name="pos-apply-discount"),
    path("pos/checkout/", views.pos_checkout, name="pos-checkout"),
    path("pos/receipt/<str:transaction_id>/", views.pos_receipt, name="pos-receipt"),
    # Settings URLs
    path("settings/", views.settings_view, name="settings"),
    path("api/theme-config/", views.api_theme_config, name="api-theme-config"),
    path("api/update-theme/", views.api_update_theme, name="api-update-theme"),
    # Chat URLs
    path("api/chats/", views.api_get_chats, name="api-chats"),
    path("api/chats/<int:chat_id>/messages/", views.api_get_messages, name="api-messages"),
    path("api/chats/<int:chat_id>/send/", views.api_send_message, name="api-send-message"),
    path("api/chats/<int:chat_id>/delete/", views.api_delete_chat, name="api-delete-chat"),
    path("api/chats/group/", views.api_get_or_create_group_chat, name="api-group-chat"),
    path("api/chats/direct/<int:user_id>/", views.api_get_or_create_direct_chat, name="api-direct-chat"),
    path("api/chats/staff/", views.api_get_staff_members, name="api-staff-members"),
]
