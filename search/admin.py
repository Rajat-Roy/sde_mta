from django.contrib import admin
from .models import SearchQuery, SearchResult


@admin.register(SearchQuery)
class SearchQueryAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'search_type', 'query_text', 'results_count', 'created_at']
    list_filter = ['search_type', 'created_at']
    search_fields = ['query_text', 'user__username']
    readonly_fields = ['created_at']


@admin.register(SearchResult)
class SearchResultAdmin(admin.ModelAdmin):
    list_display = ['id', 'search_query', 'product', 'rank_position', 'similarity_score', 'distance_km']
    list_filter = ['was_clicked', 'was_purchased']
    readonly_fields = ['created_at']
