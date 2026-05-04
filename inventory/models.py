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
    
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
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
