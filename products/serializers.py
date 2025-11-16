from rest_framework import serializers
from .models import Category, Product, ProductImage, Review, ContactMessage
from users.models import User


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model."""

    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'parent', 'created_at']
        read_only_fields = ['created_at']


class ProductImageSerializer(serializers.ModelSerializer):
    """Serializer for ProductImage model."""

    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'is_primary', 'caption', 'created_at']
        read_only_fields = ['created_at']


class ProductListSerializer(serializers.ModelSerializer):
    """Serializer for Product list view."""
    category_name = serializers.CharField(source='category.name', read_only=True)
    seller_name = serializers.CharField(source='seller.username', read_only=True)
    primary_image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'price', 'quantity', 'unit',
            'category_name', 'seller_name', 'district', 'is_active',
            'primary_image', 'created_at'
        ]
        read_only_fields = ['created_at']

    def get_primary_image(self, obj):
        primary_img = obj.images.filter(is_primary=True).first()
        if primary_img:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(primary_img.image.url)
        return None


class ProductDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for Product."""
    category = CategorySerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    seller_name = serializers.CharField(source='seller.username', read_only=True)
    seller_phone = serializers.CharField(source='seller.phone_number', read_only=True)
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'category', 'price', 'quantity', 'unit',
            'latitude', 'longitude', 'address', 'district',
            'listing_type', 'input_method', 'ai_metadata',
            'is_active', 'is_sold', 'images',
            'seller_name', 'seller_phone',
            'average_rating', 'review_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_average_rating(self, obj):
        reviews = obj.reviews.all()
        if reviews:
            return sum(r.rating for r in reviews) / len(reviews)
        return None

    def get_review_count(self, obj):
        return obj.reviews.count()


class ProductCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating products manually (not via AI)."""

    class Meta:
        model = Product
        fields = [
            'name', 'description', 'category', 'price', 'quantity', 'unit',
            'latitude', 'longitude', 'address', 'district'
        ]

    def create(self, validated_data):
        # Set seller from request user
        validated_data['seller'] = self.context['request'].user
        validated_data['input_method'] = 'text'
        return super().create(validated_data)


class ReviewSerializer(serializers.ModelSerializer):
    """Serializer for Review model."""
    buyer_name = serializers.CharField(source='buyer.username', read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'product', 'buyer_name', 'rating', 'comment', 'created_at']
        read_only_fields = ['created_at', 'buyer_name']

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value


class ContactMessageSerializer(serializers.ModelSerializer):
    """Serializer for ContactMessage model."""
    sender_name = serializers.CharField(source='sender.username', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = ContactMessage
        fields = ['id', 'product', 'sender_name', 'product_name', 'name', 'email', 'phone', 'message', 'created_at']
        read_only_fields = ['created_at', 'sender_name', 'product_name']

    def create(self, validated_data):
        # Set sender from request user
        validated_data['sender'] = self.context['request'].user
        return super().create(validated_data)
