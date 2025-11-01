"""
URL configuration for marketplace project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

from search.views import MultimodalSearchView
from ai_ingestion.views import CreateIngestionJobView, IngestionJobStatusView, PreviewImagesView, ExtractProductDetailsView
import ai_ingestion.views
import search.views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Home page
    path('', TemplateView.as_view(template_name='home.html'), name='home'),

    # Products app (includes template and API views)
    path('products/', include('products.urls')),

    # Search
    path('search/', include([
        path('', search.views.search_view, name='search'),
        path('api/', MultimodalSearchView.as_view(), name='api_search'),
    ])),

    # AI Ingestion
    path('ingest/', include([
        path('', ai_ingestion.views.upload_view, name='upload'),
        path('api/extract/', ExtractProductDetailsView.as_view(), name='extract_details'),
        path('api/create/', CreateIngestionJobView.as_view(), name='create_ingestion_job'),
        path('api/status/<int:job_id>/', IngestionJobStatusView.as_view(), name='ingestion_job_status'),
        path('api/preview-images/', PreviewImagesView.as_view(), name='preview_images'),
    ])),

    # Django REST Framework browsable API auth
    path('api-auth/', include('rest_framework.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
