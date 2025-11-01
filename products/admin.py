from django.contrib import admin
from .models import Category, Product, ProductImage, Review


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'created_at']
    search_fields = ['name']
    list_filter = ['parent']


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'seller', 'category', 'price', 'district', 'is_active', 'created_at']
    list_filter = ['category', 'district', 'is_active', 'input_method', 'listing_type']
    search_fields = ['name', 'description', 'seller__username']
    inlines = [ProductImageInline]
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'buyer', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['product__name', 'buyer__username', 'comment']
