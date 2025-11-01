from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'user_type', 'district', 'is_verified_seller', 'is_staff']
    list_filter = ['user_type', 'is_verified_seller', 'is_staff', 'district']
    search_fields = ['username', 'email', 'phone_number', 'district']

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('user_type', 'phone_number', 'district', 'latitude', 'longitude', 'address', 'profile_image', 'is_verified_seller')
        }),
    )
