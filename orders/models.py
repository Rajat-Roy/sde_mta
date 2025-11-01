from django.db import models
from django.conf import settings
from products.models import Product
import uuid


class Order(models.Model):
    """Order management for marketplace transactions."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    order_number = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sales')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Pricing
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    # Delivery information
    delivery_address = models.TextField()
    delivery_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    delivery_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # Notes
    buyer_notes = models.TextField(blank=True, null=True)
    seller_notes = models.TextField(blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Order {self.order_number} - {self.buyer.username}"

    class Meta:
        db_table = 'orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['buyer', 'status']),
            models.Index(fields=['seller', 'status']),
            models.Index(fields=['-created_at']),
        ]


class OrderItem(models.Model):
    """Individual items within an order."""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='order_items')

    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    # Snapshot of product details at time of order
    product_name = models.CharField(max_length=255)
    product_description = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product_name} x {self.quantity} in Order {self.order.order_number}"

    def save(self, *args, **kwargs):
        # Calculate total price
        self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'order_items'


class DeliveryTracking(models.Model):
    """Track delivery status and updates."""
    STATUS_CHOICES = [
        ('preparing', 'Preparing'),
        ('ready', 'Ready for Pickup'),
        ('in_transit', 'In Transit'),
        ('nearby', 'Nearby'),
        ('delivered', 'Delivered'),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='tracking')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='preparing')
    message = models.TextField()

    # Location tracking (optional)
    current_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    current_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.order.order_number} - {self.get_status_display()}"

    class Meta:
        db_table = 'delivery_tracking'
        ordering = ['-created_at']


class Invoice(models.Model):
    """Generated invoices for completed orders."""
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='invoice')
    invoice_number = models.CharField(max_length=50, unique=True)

    # Invoice details
    invoice_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(null=True, blank=True)

    # Payment status
    is_paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)
    payment_method = models.CharField(max_length=50, blank=True, null=True)

    # Additional notes
    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Invoice {self.invoice_number} for Order {self.order.order_number}"

    class Meta:
        db_table = 'invoices'
        ordering = ['-created_at']
