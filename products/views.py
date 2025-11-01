from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from django.shortcuts import render

from .models import Category, Product, ProductImage, Review
from .serializers import (
    CategorySerializer, ProductListSerializer, ProductDetailSerializer,
    ProductCreateSerializer, ProductImageSerializer, ReviewSerializer
)


# Template views
def product_list_view(request):
    """Template view for product listing."""
    return render(request, 'products/product_list.html')


def product_detail_view(request, pk):
    """Template view for product detail."""
    return render(request, 'products/product_detail.html', {'product_id': pk})


# API ViewSets
class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing categories."""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class ProductViewSet(viewsets.ModelViewSet):
    """ViewSet for Product CRUD operations with optimized queries."""
    queryset = Product.objects.filter(is_active=True).select_related('category', 'seller').prefetch_related('images', 'reviews')
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'category__name']
    ordering_fields = ['created_at', 'price', 'name']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return ProductListSerializer
        elif self.action == 'create':
            return ProductCreateSerializer
        return ProductDetailSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        district = self.request.query_params.get('district')
        if district:
            queryset = queryset.filter(district=district)
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__name=category)
        return queryset

    @action(detail=False, methods=['get'])
    def my_products(self, request):
        """Get products listed by the current user."""
        products = Product.objects.filter(seller=request.user)
        serializer = ProductListSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)


class ReviewViewSet(viewsets.ModelViewSet):
    """ViewSet for product reviews."""
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(buyer=self.request.user)
