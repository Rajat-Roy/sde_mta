from django.db import models
from django.conf import settings
import json


class Category(models.Model):
    """Product categories for organization and filtering."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subcategories')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'categories'
        verbose_name_plural = 'Categories'
        ordering = ['name']


class Product(models.Model):
    """
    Main product model supporting multimodal inputs (voice, image, text).
    Products are created through AI ingestion pipeline.
    """
    LISTING_TYPE_CHOICES = [
        ('regular', 'Regular Seller'),
        ('onetime', 'One-time Seller'),
    ]

    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='products')

    # Basic product information
    name = models.CharField(max_length=255)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')

    # Pricing and inventory
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    unit = models.CharField(max_length=50, default='piece')  # kg, piece, dozen, etc.

    # Location (inherited from seller but can be different)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    address = models.TextField(blank=True, null=True)
    district = models.CharField(max_length=100)

    # Multimodal input tracking
    listing_type = models.CharField(max_length=10, choices=LISTING_TYPE_CHOICES, default='regular')
    input_method = models.CharField(max_length=20)  # voice, image, text
    original_input = models.TextField(blank=True, null=True)  # Store original voice/text input

    # AI-generated metadata (stored as JSON)
    ai_metadata = models.JSONField(default=dict, blank=True)

    # Search optimization (vector embeddings - stored as JSON array)
    embedding = models.JSONField(default=list, blank=True)

    # Product status
    is_active = models.BooleanField(default=True)
    is_sold = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.seller.username}"

    class Meta:
        db_table = 'products'
        ordering = ['-created_at']
        indexes = [
            # Single column indexes for filtering
            models.Index(fields=['district'], name='idx_product_district'),
            models.Index(fields=['category'], name='idx_product_category'),
            models.Index(fields=['is_active'], name='idx_product_active'),
            models.Index(fields=['-created_at'], name='idx_product_created'),
            models.Index(fields=['seller'], name='idx_product_seller'),
            # Composite indexes for common query patterns
            models.Index(fields=['district', 'is_active'], name='idx_product_district_active'),
            models.Index(fields=['category', 'is_active'], name='idx_product_category_active'),
            models.Index(fields=['district', 'category', 'is_active'], name='idx_product_search'),
            models.Index(fields=['seller', 'is_active'], name='idx_product_seller_active'),
        ]


class ProductImage(models.Model):
    """Multiple images per product for better visualization."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    is_primary = models.BooleanField(default=False)
    caption = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.product.name}"

    class Meta:
        db_table = 'product_images'
        ordering = ['-is_primary', 'created_at']


class Review(models.Model):
    """Customer reviews and ratings for products."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')

    rating = models.PositiveSmallIntegerField()  # 1-5 stars
    comment = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.buyer.username} - {self.product.name} ({self.rating}★)"

    class Meta:
        db_table = 'reviews'
        ordering = ['-created_at']
        unique_together = ['product', 'buyer']
