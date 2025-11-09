from django.db import models
from django.conf import settings


class SearchQuery(models.Model):
    """Track user search queries for analytics and improvement."""
    SEARCH_TYPE_CHOICES = [
        ('text', 'Text Search'),
        ('voice', 'Voice Search'),
        ('image', 'Image Search'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='searches')

    # Search details
    search_type = models.CharField(max_length=10, choices=SEARCH_TYPE_CHOICES)
    query_text = models.TextField()  # Converted text from voice or description from image
    original_query = models.TextField(blank=True, null=True)  # Store original input if different

    # Search parameters
    district_filter = models.CharField(max_length=100, blank=True, null=True)
    category_filter = models.CharField(max_length=100, blank=True, null=True)
    max_distance_km = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    # Location context
    search_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    search_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # Search embedding for vector similarity
    query_embedding = models.JSONField(default=list, blank=True)

    # Results metadata
    results_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_search_type_display()} - {self.query_text[:50]}"

    class Meta:
        db_table = 'search_queries'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['user', '-created_at']),
        ]


class SearchResult(models.Model):
    """Track individual search results for analytics."""
    search_query = models.ForeignKey(SearchQuery, on_delete=models.CASCADE, related_name='results')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)

    # Ranking metrics
    rank_position = models.PositiveIntegerField()
    similarity_score = models.FloatField()  # Vector similarity score
    distance_km = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)  # Geo distance

    # User interaction tracking
    was_clicked = models.BooleanField(default=False)
    was_purchased = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Result #{self.rank_position} for search {self.search_query.id}"

    class Meta:
        db_table = 'search_results'
        ordering = ['rank_position']
        unique_together = ['search_query', 'product']
