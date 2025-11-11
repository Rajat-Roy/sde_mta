"""
Mock AI services for performance testing and development.
Returns realistic fake data without making external API calls.
"""
import time
import random
import numpy as np
from typing import Dict, Any, List, Optional


class MockGeminiService:
    """
    Mock implementation of GeminiIngestionService for testing.
    Returns realistic fake data in <100ms without making API calls.
    """

    # Sample data pools for generating realistic responses
    SAMPLE_PRODUCTS = [
        {
            'name': 'Fresh Tomatoes',
            'category': 'Vegetables',
            'unit': 'kg',
            'price_range': (30, 60),
            'description': 'Fresh organic tomatoes, locally sourced. Rich in vitamins and perfect for cooking.'
        },
        {
            'name': 'Samsung Galaxy S24 Ultra',
            'category': 'Mobile Phones',
            'unit': 'piece',
            'price_range': (120000, 135000),
            'description': 'Flagship smartphone with 200MP camera, S Pen, and powerful Snapdragon processor.'
        },
        {
            'name': 'HP LaserJet Printer',
            'category': 'Electronics',
            'unit': 'piece',
            'price_range': (8000, 15000),
            'description': 'Professional laser printer with wireless connectivity and fast printing speeds.'
        },
        {
            'name': 'Rice (Basmati)',
            'category': 'Grains',
            'unit': 'kg',
            'price_range': (60, 100),
            'description': 'Premium quality basmati rice with long grains and aromatic flavor.'
        },
        {
            'name': 'Leather Wallet',
            'category': 'Accessories',
            'unit': 'piece',
            'price_range': (500, 2000),
            'description': 'Genuine leather wallet with multiple card slots and coin pocket.'
        }
    ]

    SAMPLE_CATEGORIES = [
        'Vegetables', 'Fruits', 'Grains', 'Electronics', 'Mobile Phones',
        'Clothing', 'Accessories', 'Furniture', 'Books', 'Toys',
        'Home Appliances', 'Groceries', 'Dairy Products', 'Bakery'
    ]

    SAMPLE_FEATURES = [
        'High quality', 'Durable', 'Affordable', 'Premium',
        'Eco-friendly', 'Locally sourced', 'Imported', 'Handmade',
        'Fast delivery', 'Warranty included', 'Brand new', 'Certified'
    ]

    SAMPLE_IMAGE_URLS = [
        'https://via.placeholder.com/300x300/FF6B6B/FFFFFF?text=Product+1',
        'https://via.placeholder.com/300x300/4ECDC4/FFFFFF?text=Product+2',
        'https://via.placeholder.com/300x300/45B7D1/FFFFFF?text=Product+3',
        'https://via.placeholder.com/300x300/FFA07A/FFFFFF?text=Product+4',
    ]

    def __init__(self):
        """Initialize mock service (no external dependencies)."""
        self.model_name = 'mock-gemini-2.0-flash-lite'
        print("[MockGeminiService] Initialized - Using mock AI responses for testing")

    def process_text_input(self, text: str, user_location: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Mock text processing - extracts product info from text.
        Returns realistic data in <50ms.
        """
        start_time = time.time()

        # Simulate some processing time (10-50ms)
        time.sleep(random.uniform(0.01, 0.05))

        # Try to extract product info from text, or use random sample
        extracted_data = self._extract_from_text(text)

        processing_time = time.time() - start_time

        return {
            'success': True,
            'data': extracted_data,
            'model_used': self.model_name,
            'processing_time': processing_time,
            'mock': True
        }

    def process_image_input(self, image_path: str, additional_text: str = "") -> Dict[str, Any]:
        """
        Mock image processing - analyzes product image.
        Returns realistic data in <50ms.
        """
        start_time = time.time()

        # Simulate image processing time (20-60ms)
        time.sleep(random.uniform(0.02, 0.06))

        # Use additional text if provided, otherwise random product
        if additional_text:
            extracted_data = self._extract_from_text(additional_text)
        else:
            extracted_data = self._get_random_product()

        processing_time = time.time() - start_time

        return {
            'success': True,
            'data': extracted_data,
            'model_used': self.model_name,
            'processing_time': processing_time,
            'mock': True
        }

    def process_voice_input(self, audio_file_path: str) -> Dict[str, Any]:
        """
        Mock voice processing - transcribes and extracts product info.
        Returns realistic data in <100ms.
        """
        start_time = time.time()

        # Simulate transcription + extraction time (50-100ms)
        time.sleep(random.uniform(0.05, 0.1))

        # Generate mock transcription
        sample_product = random.choice(self.SAMPLE_PRODUCTS)
        transcribed_text = f"I want to sell {sample_product['name']} at {random.randint(*sample_product['price_range'])} rupees"

        extracted_data = sample_product.copy()
        extracted_data['price'] = random.randint(*sample_product['price_range'])
        extracted_data['quantity'] = random.randint(1, 50)

        processing_time = time.time() - start_time

        return {
            'success': True,
            'data': extracted_data,
            'transcribed_text': transcribed_text,
            'model_used': self.model_name,
            'processing_time': processing_time,
            'mock': True
        }

    def generate_embedding(self, text: str) -> list:
        """
        Generate mock embedding vector (768 dimensions).
        Returns consistent embeddings for same text.
        """
        # Use hash of text as seed for reproducibility
        seed = hash(text) % (2**32)
        np.random.seed(seed)

        # Generate random normalized vector
        embedding = np.random.randn(768)
        embedding = embedding / np.linalg.norm(embedding)

        return embedding.tolist()

    def search_product_images(self, product_name: str) -> List[str]:
        """
        Mock image search - returns placeholder images.
        Returns in <10ms.
        """
        # Simulate minimal search time
        time.sleep(random.uniform(0.005, 0.01))

        # Return 3-5 placeholder images
        num_images = random.randint(3, 5)
        return self.SAMPLE_IMAGE_URLS[:num_images]

    def enrich_product_from_web(self, product_name: str, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mock web enrichment - adds realistic product details.
        Returns in <50ms without making web requests.
        """
        start_time = time.time()

        # Simulate web search time (20-50ms)
        time.sleep(random.uniform(0.02, 0.05))

        # Generate mock enrichment data
        web_data = {
            'detailed_description': self._generate_description(product_name),
            'common_uses': self._generate_uses(extracted_data.get('category', 'General')),
            'typical_price_range': self._generate_price_range(extracted_data.get('price', 100)),
            'popular_brands': self._generate_brands(extracted_data.get('category', 'General')),
            'key_features': random.sample(self.SAMPLE_FEATURES, k=random.randint(3, 5)),
            'related_products': self._generate_related_products(product_name),
            'sources': ['Amazon India', 'Flipkart', 'Snapdeal']
        }

        # Get mock images
        image_urls = self.search_product_images(product_name)

        # Merge with extracted data
        enriched_data = extracted_data.copy()

        # Enhance description if web has better info
        if len(web_data['detailed_description']) > len(enriched_data.get('description', '')):
            enriched_data['description'] = web_data['detailed_description']

        # Add web metadata
        enriched_data['web_enrichment'] = {
            'common_uses': web_data['common_uses'],
            'typical_price_range': web_data['typical_price_range'],
            'popular_brands': web_data['popular_brands'],
            'key_features': web_data['key_features'],
            'related_products': web_data['related_products'],
            'image_urls': image_urls,
            'sources': web_data['sources'],
            'enriched_at': time.time(),
            'processing_time': time.time() - start_time
        }

        processing_time = time.time() - start_time

        return {
            'success': True,
            'data': enriched_data,
            'web_data': web_data,
            'processing_time': processing_time,
            'mock': True
        }

    def download_product_images(self, image_urls: List[str], product_name: str) -> List[str]:
        """
        Mock image download - returns placeholder paths.
        """
        # Simulate download time
        time.sleep(random.uniform(0.01, 0.03))

        # Return mock paths (in real scenario these would be saved files)
        mock_paths = [
            f'products/mock/{product_name.replace(" ", "_")}_{i}.jpg'
            for i in range(min(len(image_urls), 3))
        ]
        return mock_paths

    # Helper methods

    def _extract_from_text(self, text: str) -> Dict[str, Any]:
        """Extract product info from text or return random sample."""
        text_lower = text.lower()

        # Try to match known products
        for product in self.SAMPLE_PRODUCTS:
            if product['name'].lower() in text_lower:
                data = product.copy()
                data['price'] = random.randint(*product['price_range'])
                data['quantity'] = self._extract_quantity(text)
                return data

        # Return random product if no match
        return self._get_random_product()

    def _get_random_product(self) -> Dict[str, Any]:
        """Generate random product data."""
        sample = random.choice(self.SAMPLE_PRODUCTS).copy()
        sample['price'] = random.randint(*sample['price_range'])
        sample['quantity'] = random.randint(1, 100)
        return sample

    def _extract_quantity(self, text: str) -> int:
        """Try to extract quantity from text."""
        import re
        numbers = re.findall(r'\d+', text)
        if numbers:
            return int(numbers[0])
        return random.randint(1, 50)

    def _generate_description(self, product_name: str) -> str:
        """Generate realistic product description."""
        templates = [
            f"{product_name} is a high-quality product suitable for daily use. Features excellent build quality and durability.",
            f"Premium {product_name} with advanced features and competitive pricing. Perfect for home and professional use.",
            f"{product_name} - Made with quality materials and designed for long-lasting performance. Great value for money.",
        ]
        return random.choice(templates)

    def _generate_uses(self, category: str) -> List[str]:
        """Generate common uses based on category."""
        uses_map = {
            'Vegetables': ['Cooking', 'Salads', 'Juicing', 'Grilling'],
            'Fruits': ['Eating fresh', 'Juicing', 'Desserts', 'Smoothies'],
            'Electronics': ['Home use', 'Office use', 'Professional work'],
            'Mobile Phones': ['Communication', 'Photography', 'Entertainment', 'Work'],
            'default': ['General use', 'Daily activities', 'Personal use']
        }
        uses = uses_map.get(category, uses_map['default'])
        return random.sample(uses, k=min(len(uses), 3))

    def _generate_price_range(self, base_price: float) -> str:
        """Generate price range around base price."""
        low = int(base_price * 0.8)
        high = int(base_price * 1.2)
        return f"₹{low} - ₹{high}"

    def _generate_brands(self, category: str) -> List[str]:
        """Generate popular brands for category."""
        brands_map = {
            'Mobile Phones': ['Samsung', 'Apple', 'OnePlus', 'Xiaomi'],
            'Electronics': ['HP', 'Dell', 'Sony', 'LG'],
            'Clothing': ['Nike', 'Adidas', 'Zara', 'H&M'],
            'default': ['Generic Brand A', 'Generic Brand B', 'Generic Brand C']
        }
        brands = brands_map.get(category, brands_map['default'])
        return random.sample(brands, k=min(len(brands), 3))

    def _generate_related_products(self, product_name: str) -> List[str]:
        """Generate related product names."""
        return [
            f"Premium {product_name}",
            f"{product_name} Pro",
            f"Budget {product_name}",
        ]
