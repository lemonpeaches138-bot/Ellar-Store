from decimal import Decimal

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


class Product(models.Model):
    class ProductType(models.TextChoices):
        CANNED_GOODS = "CANNED", "Canned Goods"
        FROZEN_GOODS = "FROZEN", "Frozen Goods"
        CLOTHES = "CLOTHES", "Clothes"
        SCHOOL_SUPPLIES = "SCHOOL", "School Supplies"
        HARDWARE = "HARDWARE", "Hardware Supplies"
        SOAPS_WASHING = "SOAPS", "Laundry and Bath Care"
        WOMEN_CARE = "WOMENCARE", "Feminine Care"
        CLEANING_PRODUCTS = "CLEANING", "Household Cleaning Supplies"
        BEVERAGES = "BEVERAGES", "Beverages"
        SNACKS = "SNACKS", "Snacks"
        NOODLES = "NOODLES", "Noodles"
        PACKAGED_COFFEE = "COFFEE", "Packaged Coffee"
        PACKAGED_JUICE = "JUICE", "Packaged Juice"
        ELECTRONICS = "ELECTRONICS", "Electronics"
        OTHER = "OTHER", "Other"

    name = models.CharField(max_length=120)
    sku = models.CharField(max_length=50, unique=True)
    product_type = models.CharField(
        max_length=20,
        choices=ProductType.choices,
        default=ProductType.OTHER,
    )
    quantity = models.PositiveIntegerField(default=0)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="selling price")
    expiration_date = models.DateField(blank=True, null=True)
    reorder_level = models.PositiveIntegerField(default=5)
    total_sold = models.PositiveIntegerField(default=0, help_text="Total units sold")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.sku})"

    @staticmethod
    def _as_decimal(value):
        if value is None:
            return Decimal("0.00")
        if isinstance(value, Decimal):
            return value
        return Decimal(str(value))

    @property
    def profit_per_unit(self):
        return self._as_decimal(self.unit_price) - self._as_decimal(self.purchase_price)

    @property
    def total_profit(self):
        return self.profit_per_unit * self.quantity


class StockMovement(models.Model):
    class MovementType(models.TextChoices):
        STOCK_IN = "IN", "Stock In"
        STOCK_OUT = "OUT", "Stock Out"

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="movements")
    movement_type = models.CharField(max_length=3, choices=MovementType.choices)
    quantity = models.PositiveIntegerField()
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.product.sku} - {self.movement_type} {self.quantity}"


class UserRegistration(models.Model):
    """Model for pending user registrations requiring admin approval."""
    class StaffRole(models.TextChoices):
        CASHIER = "cashier", "Cashier"
        INVENTORY = "inventory", "Inventory Staff"

    BRANCH_CHOICES = [
        ('main', 'Main Branch'),
        ('branch1', 'Branch 1'),
        ('branch2', 'Branch 2'),
        ('branch3', 'Branch 3'),
        ('branch4', 'Branch 4'),
    ]

    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    phone = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=255, blank=True)
    branch = models.CharField(max_length=10, choices=BRANCH_CHOICES, default='main')
    staff_role = models.CharField(max_length=20, choices=StaffRole.choices, default=StaffRole.CASHIER)
    password = models.CharField(max_length=128)  # Will store hashed password
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_registrations')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.username} - {'Approved' if self.is_approved else 'Pending'}"


class Notification(models.Model):
    """Model for tracking system notifications for admin."""

    class NotificationType(models.TextChoices):
        STOCK_IN = 'STOCK_IN', 'Stock In'
        STOCK_OUT = 'STOCK_OUT', 'Stock Out'
        SALE = 'SALE', 'Sale'
        LOW_STOCK = 'LOW_STOCK', 'Low Stock'
        USER_REGISTERED = 'USER_REGISTERED', 'User Registered'
        USER_APPROVED = 'USER_APPROVED', 'User Approved'

    type = models.CharField(max_length=20, choices=NotificationType.choices)
    title = models.CharField(max_length=200)
    message = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_notifications')
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    # Optional related objects
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    transaction = models.ForeignKey('Transaction', on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.type} - {self.title}"


class Transaction(models.Model):
    transaction_id = models.CharField(max_length=50, unique=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    cash_received = models.DecimalField(max_digits=12, decimal_places=2)
    change = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Transaction {self.transaction_id} - {self.total}"


class TransactionItem(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"


class UserProfile(models.Model):
    """Store user-specific preferences including theme customization."""
    class StaffRole(models.TextChoices):
        CASHIER = "cashier", "Cashier"
        INVENTORY = "inventory", "Inventory Staff"

    COLOR_CHOICES = [
        ('pink', 'Pink'),
        ('blue', 'Blue'),
        ('green', 'Green'),
        ('purple', 'Purple'),
        ('orange', 'Orange'),
        ('red', 'Red'),
        ('teal', 'Teal'),
        ('indigo', 'Indigo'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    staff_role = models.CharField(max_length=20, choices=StaffRole.choices, default=StaffRole.CASHIER)
    address = models.CharField(max_length=255, blank=True)
    birthday = models.DateField(blank=True, null=True)
    dark_mode = models.BooleanField(default=False)
    primary_color = models.CharField(max_length=20, choices=COLOR_CHOICES, default='pink')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile for {self.user.username}"

    @property
    def age(self):
        """Return the user's age based on birthday, if available."""
        if not self.birthday:
            return None

        today = timezone.localdate()
        return today.year - self.birthday.year - (
            (today.month, today.day) < (self.birthday.month, self.birthday.day)
        )

    @property
    def theme_config(self):
        """Return theme configuration for frontend."""
        color_map = {
            'pink': {'hex': '#ec4899', 'gradient': 'linear-gradient(135deg, #ec4899 0%, #f472b6 100%)'},
            'blue': {'hex': '#3b82f6', 'gradient': 'linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%)'},
            'green': {'hex': '#10b981', 'gradient': 'linear-gradient(135deg, #10b981 0%, #34d399 100%)'},
            'purple': {'hex': '#8b5cf6', 'gradient': 'linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%)'},
            'orange': {'hex': '#f97316', 'gradient': 'linear-gradient(135deg, #f97316 0%, #fb923c 100%)'},
            'red': {'hex': '#ef4444', 'gradient': 'linear-gradient(135deg, #ef4444 0%, #f87171 100%)'},
            'teal': {'hex': '#14b8a6', 'gradient': 'linear-gradient(135deg, #14b8a6 0%, #2dd4bf 100%)'},
            'indigo': {'hex': '#6366f1', 'gradient': 'linear-gradient(135deg, #6366f1 0%, #818cf8 100%)'},
        }

        config = color_map.get(self.primary_color, color_map['pink'])
        hex_value = config['hex'].lstrip('#')
        rgb_value = ', '.join(
            str(int(hex_value[index:index + 2], 16))
            for index in (0, 2, 4)
        )
        return {
            'dark_mode': self.dark_mode,
            'primary_color': self.primary_color,
            'hex': config['hex'],
            'gradient': config['gradient'],
            'rgb': rgb_value,
        }


class Chat(models.Model):
    """Model for chat conversations (group or one-to-one)."""
    class ChatType(models.TextChoices):
        GROUP = 'GROUP', 'Group Chat'
        DIRECT = 'DIRECT', 'Direct Chat'

    chat_type = models.CharField(max_length=10, choices=ChatType.choices, default=ChatType.DIRECT)
    name = models.CharField(max_length=255, blank=True, help_text="For group chats")
    participants = models.ManyToManyField(User, related_name='chats')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        if self.chat_type == self.ChatType.GROUP:
            return f"Group: {self.name}"
        else:
            return f"Chat between {', '.join([u.username for u in self.participants.all()])}"

    def get_display_name(self, current_user):
        """Get chat display name for the current user."""
        if self.chat_type == self.ChatType.GROUP:
            return self.name
        else:
            # For direct chats, show the other person's name
            other_users = self.participants.exclude(id=current_user.id)
            if other_users.exists():
                return other_users.first().get_full_name() or other_users.first().username
            return "Chat"


class Message(models.Model):
    """Model for individual chat messages."""
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender.username} in {self.chat}: {self.content[:50]}"


class ChatReadState(models.Model):
    """Track the last message seen by each user in each chat."""
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='read_states')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_read_states')
    last_read_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('chat', 'user')

    def __str__(self):
        return f"{self.user.username} read {self.chat} at {self.last_read_at}"
