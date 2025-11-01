from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    Supports both sellers and buyers in the district marketplace.
    """
    USER_TYPE_CHOICES = [
        ('buyer', 'Buyer'),
        ('seller', 'Seller'),
        ('both', 'Both'),
    ]

    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='buyer')
    phone_number = models.CharField(max_length=15, blank=True, null=True)

    # Location fields for district-level commerce
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    address = models.TextField(blank=True, null=True)
    district = models.CharField(max_length=100, blank=True, null=True)

    # Profile fields
    profile_image = models.ImageField(upload_to='profiles/', null=True, blank=True)
    is_verified_seller = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"

    class Meta:
        db_table = 'users'
        ordering = ['-created_at']
