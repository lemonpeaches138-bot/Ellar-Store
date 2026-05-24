from django.contrib import admin

from .models import Product, StockMovement, Transaction, TransactionItem, UserProfile, UserRegistration, Notification, Chat, Message


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
    list_display = ("user", "staff_role", "dark_mode", "primary_color", "updated_at")
    search_fields = ("user__username",)
    list_filter = ("staff_role", "dark_mode", "primary_color")
    readonly_fields = ("created_at", "updated_at")


@admin.register(UserRegistration)
class UserRegistrationAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "staff_role", "branch", "is_approved", "created_at")
    search_fields = ("username", "email", "first_name", "last_name")
    list_filter = ("staff_role", "is_approved", "branch", "created_at")
    readonly_fields = ("created_at", "approved_at", "approved_by")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "type", "created_by", "is_read", "created_at")
    search_fields = ("title", "message")
    list_filter = ("type", "is_read", "created_at")
    readonly_fields = ("created_at",)


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ("sender", "created_at")


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ("get_display_name_admin", "chat_type", "get_participant_count", "created_at", "updated_at")
    search_fields = ("name",)
    list_filter = ("chat_type", "created_at")
    readonly_fields = ("created_at", "updated_at")
    inlines = [MessageInline]

    def get_display_name_admin(self, obj):
        if obj.chat_type == Chat.ChatType.GROUP:
            return f"Group: {obj.name}"
        else:
            return f"Direct: {', '.join([u.username for u in obj.participants.all()])}"
    get_display_name_admin.short_description = "Chat"

    def get_participant_count(self, obj):
        return obj.participants.count()
    get_participant_count.short_description = "Participants"


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("sender", "get_chat_display", "content_preview", "created_at", "is_read")
    search_fields = ("sender__username", "content", "chat__name")
    list_filter = ("created_at", "is_read")
    readonly_fields = ("sender", "created_at")

    def get_chat_display(self, obj):
        return str(obj.chat)
    get_chat_display.short_description = "Chat"

    def content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
    content_preview.short_description = "Message"
