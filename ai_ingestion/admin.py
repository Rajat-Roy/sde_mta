from django.contrib import admin
from .models import IngestionJob


@admin.register(IngestionJob)
class IngestionJobAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'input_type', 'status', 'created_product', 'created_at']
    list_filter = ['input_type', 'status', 'created_at']
    search_fields = ['user__username', 'input_text']
    readonly_fields = ['created_at', 'updated_at', 'completed_at']
