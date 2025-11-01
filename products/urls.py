from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'categories', views.CategoryViewSet, basename='category')
router.register(r'products', views.ProductViewSet, basename='product')
router.register(r'reviews', views.ReviewViewSet, basename='review')

app_name = 'products'

urlpatterns = [
    # Template views
    path('', views.product_list_view, name='product_list'),
    path('<int:pk>/', views.product_detail_view, name='product_detail'),

    # API endpoints
    path('api/', include(router.urls)),
]
