from django.contrib import admin

from .models import Product, StockMovement, Transaction, TransactionItem, UserProfile, UserRegistration, Notification


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "sku",
        "product_type",
        "quantity",
        "purchase_price",
        "unit_price",
        "expiration_date",
        "profit_per_unit",
        "reorder_level",
        "updated_at",
    )
    search_fields = ("name", "sku")
    list_filter = ("product_type", "expiration_date", "updated_at")


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ("product", "movement_type", "quantity", "created_at")
    search_fields = ("product__name", "product__sku", "note")
    list_filter = ("movement_type", "created_at")


class TransactionItemInline(admin.TabularInline):
    model = TransactionItem
    extra = 0
    readonly_fields = ("product", "quantity", "unit_price", "subtotal")


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("transaction_id", "total", "discount", "change", "created_at")
    search_fields = ("transaction_id",)
    list_filter = ("created_at",)
    readonly_fields = ("transaction_id", "subtotal", "discount", "total", "cash_received", "change", "created_at")
    inlines = [TransactionItemInline]


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "dark_mode", "primary_color", "updated_at")
    search_fields = ("user__username",)
    list_filter = ("dark_mode", "primary_color")
    readonly_fields = ("created_at", "updated_at")


@admin.register(UserRegistration)
class UserRegistrationAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "branch", "is_approved", "created_at")
    search_fields = ("username", "email", "first_name", "last_name")
    list_filter = ("is_approved", "branch", "created_at")
    readonly_fields = ("created_at", "approved_at", "approved_by")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "type", "created_by", "is_read", "created_at")
    search_fields = ("title", "message")
    list_filter = ("type", "is_read", "created_at")
    readonly_fields = ("created_at",)