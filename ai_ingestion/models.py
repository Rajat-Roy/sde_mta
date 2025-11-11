from django.db import models
from django.conf import settings


class IngestionJob(models.Model):
    """Track AI-powered ingestion jobs for multimodal inputs."""
    INPUT_TYPE_CHOICES = [
        ('voice', 'Voice Input'),
        ('image', 'Image Input'),
        ('text', 'Text Input'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ingestion_jobs')

    # Input details
    input_type = models.CharField(max_length=10, choices=INPUT_TYPE_CHOICES)
    input_file = models.FileField(upload_to='ingestion/', null=True, blank=True)  # For voice/image files
    input_text = models.TextField(blank=True, null=True)  # For text input or transcription

    # Processing status
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True, null=True)

    # AI processing results
    extracted_data = models.JSONField(default=dict, blank=True)  # Structured data extracted by AI
    ai_confidence = models.FloatField(null=True, blank=True)  # Confidence score from AI
    ai_metadata = models.JSONField(default=dict, blank=True)  # Additional AI metadata (e.g., downloaded images)

    # Processing metadata
    processing_time_seconds = models.FloatField(null=True, blank=True)
    gemini_model_used = models.CharField(max_length=100, blank=True, null=True)

    # Related product (if created)
    created_product = models.ForeignKey('products.Product', on_delete=models.SET_NULL, null=True, blank=True, related_name='ingestion_source')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.get_input_type_display()} - {self.get_status_display()} - {self.user.username}"

    class Meta:
        db_table = 'ingestion_jobs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['-created_at']),
        ]
