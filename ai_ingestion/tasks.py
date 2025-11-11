"""
Celery tasks for asynchronous AI ingestion processing.
"""

from celery import shared_task
from django.utils import timezone
from django.conf import settings
import time
import os

from .models import IngestionJob
from .services import GeminiIngestionService
from .mock_services import MockGeminiService
from products.models import Product, ProductImage, Category


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


@shared_task
def process_ingestion_job(job_id: int):
    """
    Process an ingestion job asynchronously.

    Args:
        job_id: ID of the IngestionJob to process
    """
    try:
        job = IngestionJob.objects.get(id=job_id)
    except IngestionJob.DoesNotExist:
        return {'success': False, 'error': 'Job not found'}

    # Update status to processing
    job.status = 'processing'
    job.save()

    start_time = time.time()
    service = get_ai_service()

    try:
        # Process based on input type
        if job.input_type == 'text':
            result = service.process_text_input(job.input_text)

        elif job.input_type == 'image':
            # Get the file path
            image_path = job.input_file.path
            additional_text = job.input_text or ""
            result = service.process_image_input(image_path, additional_text)

        elif job.input_type == 'voice':
            # Get the audio file path
            audio_path = job.input_file.path
            result = service.process_voice_input(audio_path)

        else:
            raise ValueError(f"Unknown input type: {job.input_type}")

        processing_time = time.time() - start_time

        if result['success']:
            # Store extracted data
            extracted_data = result['data']
            job.extracted_data = extracted_data
            job.ai_confidence = extracted_data.get('confidence', 0.0)
            job.processing_time_seconds = processing_time
            job.gemini_model_used = result.get('model_used', 'unknown')

            # Enrich product data from web
            product_name = extracted_data.get('name', '')
            if product_name:
                enrichment_result = service.enrich_product_from_web(product_name, extracted_data)
                if enrichment_result['success']:
                    extracted_data = enrichment_result['data']
                    job.extracted_data = extracted_data  # Update with enriched data

                    # Download product images
                    # Use user-selected images if available, otherwise use scraped images
                    selected_image_urls = job.ai_metadata.get('selected_image_urls', []) if job.ai_metadata else []

                    if selected_image_urls:
                        # User selected specific images from preview
                        image_urls = selected_image_urls
                    else:
                        # Use automatically scraped images
                        web_enrichment = extracted_data.get('web_enrichment', {})
                        image_urls = web_enrichment.get('image_urls', [])

                    if image_urls:
                        job.ai_metadata = job.ai_metadata or {}
                        job.ai_metadata['downloaded_image_paths'] = service.download_product_images(
                            image_urls, product_name
                        )

            # Create product from enriched data
            product = create_product_from_extraction(job, extracted_data)

            if product:
                job.created_product = product
                job.status = 'completed'
                job.completed_at = timezone.now()
            else:
                job.status = 'failed'
                job.error_message = 'Failed to create product from extracted data'

        else:
            job.status = 'failed'
            job.error_message = result.get('error', 'Unknown error')
            job.processing_time_seconds = processing_time

        job.save()

        return {
            'success': job.status == 'completed',
            'job_id': job.id,
            'product_id': job.created_product.id if job.created_product else None
        }

    except Exception as e:
        print(f"[Job {job_id}] Exception occurred: {str(e)}")
        import traceback
        traceback.print_exc()

        job.status = 'failed'
        job.error_message = str(e)
        job.processing_time_seconds = time.time() - start_time
        job.save()

        return {
            'success': False,
            'job_id': job.id,
            'error': str(e)
        }


def create_product_from_extraction(job: IngestionJob, extracted_data: dict) -> Product:
    """
    Create a Product from AI-extracted data.

    Args:
        job: The IngestionJob that was processed
        extracted_data: Dictionary of extracted product data

    Returns:
        Created Product instance or None
    """
    try:
        print(f"[Job {job.id}] Creating product from extracted data: {extracted_data}")
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

        # Create product
        product = Product.objects.create(
            seller=job.user,
            name=extracted_data['name'],
            description=extracted_data.get('description', ''),
            category=category,
            price=price,
            quantity=extracted_data.get('quantity', 1),
            unit=extracted_data.get('unit', 'piece'),
            latitude=job.user.latitude,
            longitude=job.user.longitude,
            address=job.user.address,
            district=job.user.district or settings.DEFAULT_DISTRICT,
            input_method=job.input_type,
            original_input=job.input_text or "",
            ai_metadata=extracted_data.get('metadata', {}),
            is_active=True
        )

        # Generate and store embedding for vector search
        service = get_ai_service()
        embedding_text = f"{product.name} {product.description} {category_name}"
        embedding = service.generate_embedding(embedding_text)
        product.embedding = embedding
        product.save()

        # If there's an image file, create ProductImage
        if job.input_type == 'image' and job.input_file:
            ProductImage.objects.create(
                product=product,
                image=job.input_file,
                is_primary=True
            )

        # Add downloaded web images
        downloaded_images = job.ai_metadata.get('downloaded_image_paths', []) if job.ai_metadata else []
        for idx, image_path in enumerate(downloaded_images):
            ProductImage.objects.create(
                product=product,
                image=image_path,
                is_primary=(idx == 0 and job.input_type != 'image')  # First web image is primary if no user image
            )

        return product

    except Exception as e:
        print(f"Error creating product: {e}")
        return None
