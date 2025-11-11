from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import render
from django.utils import timezone
import json
import time
import os

from .models import IngestionJob
from .services import GeminiIngestionService
from .mock_services import MockGeminiService
from products.models import Product, ProductImage, Category
from django.conf import settings


def get_ai_service():
    """
    Get AI service based on USE_MOCK_AI environment variable.
    Returns MockGeminiService for testing or real GeminiIngestionService.
    """
    use_mock = os.getenv('USE_MOCK_AI', 'False').lower() == 'true'
    if use_mock:
        print("[AI Service] Using MockGeminiService for fast responses")
        return MockGeminiService()
    else:
        return GeminiIngestionService()


def upload_view(request):
    """Template view for multimodal upload."""
    return render(request, 'ai_ingestion/upload.html')


class CreateIngestionJobView(APIView):
    """API view to process ingestion directly (no queue)."""
    authentication_classes = []  # Disable authentication for testing
    permission_classes = []  # Allow anyone for testing (change to [IsAuthenticated] in production)

    def post(self, request):
        """
        Process ingestion directly and create product.

        For text: {"input_type": "text", "text": "...", "selected_image_urls": [...]}
        For voice/image: file upload with input_type
        """
        input_type = request.data.get('input_type')

        if not input_type or input_type not in ['text', 'voice', 'image']:
            return Response(
                {'error': 'Valid input_type required (text, voice, image)'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get or create a test user if not authenticated
        if request.user.is_authenticated:
            user = request.user
        else:
            # Create or get a test user for unauthenticated requests
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user, created = User.objects.get_or_create(
                username='anonymous',
                defaults={
                    'email': 'anonymous@example.com',
                    'user_type': 'seller',
                    'district': settings.DEFAULT_DISTRICT,
                    'latitude': 26.2389,  # Example coordinates (Jodhpur)
                    'longitude': 73.0243,
                }
            )

        start_time = time.time()
        service = get_ai_service()

        # Get selected image URLs if provided
        selected_image_urls = request.data.get('selected_image_urls', [])

        # Get uploaded image files if provided
        uploaded_images = request.FILES.getlist('uploaded_images', [])

        try:
            # Check if user provided edited product data (from preview form)
            if request.data.get('product_name'):
                # User has edited the data, use their values directly
                extracted_data = {
                    'name': request.data.get('product_name'),
                    'description': request.data.get('product_description', ''),
                    'price': request.data.get('product_price', 0),
                    'quantity': request.data.get('product_quantity', 1),
                    'unit': request.data.get('product_unit', 'piece'),
                    'category': request.data.get('product_category', 'Uncategorized')
                }
                product_name = extracted_data['name']
            else:
                # Process based on input type
                if input_type == 'text':
                    result = service.process_text_input(request.data.get('text'))
                elif input_type == 'image':
                    # TODO: Handle image upload
                    return Response({'error': 'Image input not yet implemented'}, status=status.HTTP_501_NOT_IMPLEMENTED)
                elif input_type == 'voice':
                    # TODO: Handle voice upload
                    return Response({'error': 'Voice input not yet implemented'}, status=status.HTTP_501_NOT_IMPLEMENTED)
                else:
                    return Response({'error': f'Unknown input type: {input_type}'}, status=status.HTTP_400_BAD_REQUEST)

                if not result['success']:
                    return Response({
                        'success': False,
                        'error': result.get('error', 'Processing failed')
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                extracted_data = result['data']
                product_name = extracted_data.get('name', '')

                # Enrich product data from web if not edited by user
                if product_name:
                    enrichment_result = service.enrich_product_from_web(product_name, extracted_data)
                    if enrichment_result['success']:
                        extracted_data = enrichment_result['data']

            # Handle images
            downloaded_images = []

            # If user uploaded custom images, save them
            if uploaded_images:
                import os
                from django.core.files.storage import default_storage

                product_images_dir = os.path.join('products', 'uploaded')
                for idx, img_file in enumerate(uploaded_images[:3]):  # Max 3 images
                    # Generate filename
                    ext = os.path.splitext(img_file.name)[1]
                    filename = f"{product_name.replace(' ', '_')}_{idx}_{int(time.time())}{ext}"
                    filepath = os.path.join(product_images_dir, filename)

                    # Save file
                    saved_path = default_storage.save(filepath, img_file)
                    downloaded_images.append(saved_path)

            # Otherwise download from selected URLs
            elif selected_image_urls:
                downloaded_images = service.download_product_images(selected_image_urls, product_name)

            # Create product
            product = self._create_product(user, extracted_data, downloaded_images, input_type, request.data.get('text', ''))

            processing_time = time.time() - start_time

            if product:
                return Response({
                    'success': True,
                    'product_id': product.id,
                    'product_name': product.name,
                    'processing_time': round(processing_time, 2),
                    'message': 'Product created successfully'
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'success': False,
                    'error': 'Failed to create product'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            print(f"Error processing ingestion: {str(e)}")
            import traceback
            traceback.print_exc()

            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _create_product(self, user, extracted_data, downloaded_images, input_type, original_input):
        """Create a Product from extracted data."""
        try:
            # Validate required fields
            if not extracted_data.get('name'):
                print("Error: Product name is required")
                return None

            # Get or create category
            category_name = extracted_data.get('category', 'Uncategorized')
            category, _ = Category.objects.get_or_create(name=category_name)

            # Extract and validate price (default to 0 if not provided or invalid)
            price = extracted_data.get('price', 0)
            if price is None or price == '':
                price = 0
            try:
                price = float(price)
            except (ValueError, TypeError):
                price = 0

            # Extract and validate quantity (default to 1 if not provided or invalid)
            quantity = extracted_data.get('quantity', 1)
            if quantity is None or quantity == '':
                quantity = 1
            try:
                quantity = int(quantity)
                if quantity < 1:
                    quantity = 1
            except (ValueError, TypeError):
                quantity = 1

            # Create product
            product = Product.objects.create(
                seller=user,
                name=extracted_data['name'],
                description=extracted_data.get('description', ''),
                category=category,
                price=price,
                quantity=quantity,
                unit=extracted_data.get('unit', 'piece') or 'piece',
                latitude=user.latitude,
                longitude=user.longitude,
                address=user.address,
                district=user.district or settings.DEFAULT_DISTRICT,
                input_method=input_type,
                original_input=original_input,
                ai_metadata=extracted_data.get('metadata', {}),
                is_active=True
            )

            # Generate and store embedding for vector search
            service = get_ai_service()
            embedding_text = f"{product.name} {product.description} {category_name}"
            embedding = service.generate_embedding(embedding_text)
            product.embedding = embedding
            product.save()

            # Add downloaded web images
            for idx, image_path in enumerate(downloaded_images):
                ProductImage.objects.create(
                    product=product,
                    image=image_path,
                    is_primary=(idx == 0)  # First image is primary
                )

            return product

        except Exception as e:
            print(f"Error creating product: {e}")
            import traceback
            traceback.print_exc()
            return None


class ExtractProductDetailsView(APIView):
    """API view to extract product details without creating product."""
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        """
        Extract product details from text input.

        Request: {"text": "product description..."}
        Response: {"success": true, "extracted_data": {...}, "image_urls": [...]}
        """
        text = request.data.get('text')

        if not text:
            return Response(
                {'error': 'text is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            service = get_ai_service()

            # Extract product details
            result = service.process_text_input(text)

            if not result['success']:
                return Response({
                    'success': False,
                    'error': result.get('error', 'Extraction failed')
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            extracted_data = result['data']

            # Enrich from web
            product_name = extracted_data.get('name', '')
            image_urls = []

            if product_name:
                enrichment_result = service.enrich_product_from_web(product_name, extracted_data)
                if enrichment_result['success']:
                    extracted_data = enrichment_result['data']

                    # Get image URLs for preview
                    web_enrichment = extracted_data.get('web_enrichment', {})
                    image_urls = web_enrichment.get('image_urls', [])

            return Response({
                'success': True,
                'extracted_data': extracted_data,
                'image_urls': image_urls
            })

        except Exception as e:
            print(f"Error extracting details: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PreviewImagesView(APIView):
    """API view to preview scraped images before creating job."""
    authentication_classes = []  # Disable authentication for testing
    permission_classes = []  # Allow anyone for testing

    def post(self, request):
        """
        Scrape and return product images for user selection.

        Request body: {"product_name": "Product Name"}
        """
        product_name = request.data.get('product_name')

        if not product_name:
            return Response(
                {'error': 'product_name is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            service = get_ai_service()
            print(f"[PreviewImages] Fetching preview images for: {product_name}")

            # Get image URLs without downloading
            image_urls = service.search_product_images(product_name)

            print(f"[PreviewImages] Found {len(image_urls)} images: {image_urls}")

            return Response({
                'success': True,
                'product_name': product_name,
                'image_urls': image_urls,
                'count': len(image_urls)
            })

        except Exception as e:
            print(f"[PreviewImages] Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class IngestionJobStatusView(APIView):
    """API view to check ingestion job status."""
    authentication_classes = []  # Disable authentication for testing
    permission_classes = []  # Allow anyone for testing

    def get(self, request, job_id):
        """Get the status of an ingestion job."""
        try:
            job = IngestionJob.objects.get(id=job_id)
        except IngestionJob.DoesNotExist:
            return Response({'error': 'Job not found'}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'job_id': job.id,
            'status': job.status,
            'input_type': job.input_type,
            'error_message': job.error_message,
            'extracted_data': job.extracted_data if job.status == 'completed' else None,
            'product_id': job.created_product.id if job.created_product else None,
            'processing_time': job.processing_time_seconds,
            'created_at': job.created_at,
            'completed_at': job.completed_at
        })
