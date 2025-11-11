"""
AI Ingestion Service using Gemini Flash API.
Handles multimodal inputs (voice, image, text) to create structured product listings.
"""

import os
import json
import time
import re
import requests
from typing import Dict, Any, Optional, List
from django.conf import settings
from google import genai
from PIL import Image
import io
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

# Speech recognition is optional due to Python 3.13 compatibility issues
try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    SPEECH_RECOGNITION_AVAILABLE = False
    print("Warning: SpeechRecognition not available. Voice input will use Gemini audio API instead.")


class GeminiIngestionService:
    """Service to process multimodal inputs using Gemini API."""

    def __init__(self):
        """Initialize Gemini API."""
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model_name = 'gemini-2.0-flash-lite'

    def process_text_input(self, text: str, user_location: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Process text input to extract product information.

        Args:
            text: Raw text describing the product
            user_location: Optional dict with latitude, longitude, address

        Returns:
            Dict containing extracted product data
        """
        prompt = f"""
        Extract structured product information from the following text.
        Return ONLY a valid JSON object with these exact fields (no markdown, no code blocks):

        {{
            "name": "product name",
            "description": "detailed product description",
            "category": "suggested category",
            "price": numeric value only,
            "quantity": numeric value only,
            "unit": "piece/kg/dozen/liter/etc",
            "metadata": {{
                "keywords": ["keyword1", "keyword2"],
                "suggested_tags": ["tag1", "tag2"]
            }},
            "confidence": 0.0-1.0
        }}

        Text: {text}

        Remember: Return ONLY the JSON object, nothing else.
        """

        try:
            start_time = time.time()
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            processing_time = time.time() - start_time

            # Extract JSON from response
            result_text = response.text.strip()

            # Remove markdown code blocks if present
            if result_text.startswith('```'):
                result_text = result_text.split('```')[1]
                if result_text.startswith('json'):
                    result_text = result_text[4:].strip()

            extracted_data = json.loads(result_text)

            return {
                'success': True,
                'data': extracted_data,
                'processing_time': processing_time,
                'model_used': self.model_name
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'processing_time': 0
            }

    def process_image_input(self, image_path: str, additional_text: str = "") -> Dict[str, Any]:
        """
        Process image input to extract product information.

        Args:
            image_path: Path to the product image
            additional_text: Optional additional text description

        Returns:
            Dict containing extracted product data
        """
        prompt = f"""
        Analyze this product image and extract structured information.
        Return ONLY a valid JSON object (no markdown, no code blocks):

        {{
            "name": "product name based on what you see",
            "description": "detailed description of the product in the image",
            "category": "suggested category",
            "estimated_price_range": "price range estimate",
            "visual_attributes": {{
                "color": "color",
                "condition": "new/used",
                "features": ["feature1", "feature2"]
            }},
            "metadata": {{
                "keywords": ["keyword1", "keyword2"],
                "suggested_tags": ["tag1", "tag2"]
            }},
            "confidence": 0.0-1.0
        }}

        {f'Additional context: {additional_text}' if additional_text else ''}

        Remember: Return ONLY the JSON object, nothing else.
        """

        try:
            start_time = time.time()

            # Load and process image
            with open(image_path, 'rb') as f:
                image_data = f.read()

            # Generate content with image
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[
                    prompt,
                    {"mime_type": "image/jpeg", "data": image_data}
                ]
            )
            processing_time = time.time() - start_time

            # Extract JSON from response
            result_text = response.text.strip()

            # Remove markdown code blocks if present
            if result_text.startswith('```'):
                result_text = result_text.split('```')[1]
                if result_text.startswith('json'):
                    result_text = result_text[4:].strip()

            extracted_data = json.loads(result_text)

            return {
                'success': True,
                'data': extracted_data,
                'processing_time': processing_time,
                'model_used': self.model_name
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'processing_time': 0
            }

    def process_voice_input(self, audio_file_path: str) -> Dict[str, Any]:
        """
        Process voice input to extract product information.
        First converts speech to text, then processes the text.

        Args:
            audio_file_path: Path to the audio file

        Returns:
            Dict containing extracted product data
        """
        if not SPEECH_RECOGNITION_AVAILABLE:
            return {
                'success': False,
                'error': 'Speech recognition not available in Python 3.13+. Please use text or image input.',
                'processing_time': 0
            }

        try:
            # Convert audio to text using SpeechRecognition
            recognizer = sr.Recognizer()

            # Load audio file
            audio_file = sr.AudioFile(audio_file_path)

            with audio_file as source:
                audio_data = recognizer.record(source)

            # Convert speech to text (using Google Speech Recognition)
            try:
                transcribed_text = recognizer.recognize_google(audio_data)
            except sr.UnknownValueError:
                return {
                    'success': False,
                    'error': 'Could not understand audio',
                    'processing_time': 0
                }
            except sr.RequestError as e:
                return {
                    'success': False,
                    'error': f'Speech recognition service error: {str(e)}',
                    'processing_time': 0
                }

            # Now process the transcribed text
            result = self.process_text_input(transcribed_text)

            if result['success']:
                result['transcribed_text'] = transcribed_text

            return result

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'processing_time': 0
            }

    def generate_embedding(self, text: str) -> list:
        """
        Generate text embedding for vector similarity search.

        Args:
            text: Text to generate embedding for

        Returns:
            List of floats representing the embedding
        """
        try:
            # Use Gemini's embedding model with new API
            response = self.client.models.embed_content(
                model="text-embedding-004",
                contents=text
            )
            return response.embeddings[0].values

        except Exception as e:
            # Fallback to simple embedding if Gemini fails
            print(f"Embedding generation failed: {e}")
            return []

    def generate_search_embedding(self, query: str) -> list:
        """
        Generate embedding for search query.

        Args:
            query: Search query text

        Returns:
            List of floats representing the embedding
        """
        try:
            response = self.client.models.embed_content(
                model="text-embedding-004",
                contents=query
            )
            return response.embeddings[0].values

        except Exception as e:
            print(f"Search embedding generation failed: {e}")
            return []

    def get_official_product_pages(self, product_name: str) -> List[str]:
        """
        Use Gemini to find official product pages for a product.

        Args:
            product_name: Name of the product

        Returns:
            List of official product page URLs
        """
        try:
            prompt = f"""
            Search for product pages for "{product_name}".

            Return ONLY a JSON array of direct website URLs (no markdown, no code blocks):
            ["https://www.example.com/product1", "https://www.example2.com/product2"]

            Requirements:
            1. Return ACTUAL website URLs (e.g., https://www.hp.com/..., https://www.amazon.in/..., https://www.flipkart.com/...)
            2. NOT redirect or API URLs
            3. Include:
               - Official manufacturer website (if available)
               - Indian e-commerce marketplaces: Amazon India, Flipkart, Snapdeal, Croma, Reliance Digital
               - International marketplaces: Amazon.com, eBay
            4. Prioritize Indian marketplaces
            5. Maximum 5 URLs
            6. URLs must start with https://www.

            Return ONLY the JSON array, nothing else.
            """

            # Don't use grounding here - we want Gemini to suggest likely URLs based on knowledge
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )

            result_text = response.text.strip()

            # Remove markdown code blocks if present
            if result_text.startswith('```'):
                result_text = result_text.split('```')[1]
                if result_text.startswith('json'):
                    result_text = result_text[4:].strip()

            urls = json.loads(result_text)
            print(f"Found {len(urls)} product pages for '{product_name}': {urls}")
            return urls[:5]  # Return up to 5 URLs

        except Exception as e:
            print(f"Failed to get official pages: {e}")
            return []

    def scrape_images_from_page(self, url: str) -> List[str]:
        """
        Scrape product images from a webpage.

        Args:
            url: URL of the product page

        Returns:
            List of image URLs found on the page
        """
        image_urls = []
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }

            response = requests.get(url, headers=headers, timeout=20)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                # Find all img tags
                for img in soup.find_all('img'):
                    # Try multiple attributes for image source
                    src = (img.get('src') or
                          img.get('data-src') or
                          img.get('data-lazy-src') or
                          img.get('data-original') or
                          (img.get('srcset', '').split(',')[0].split()[0] if img.get('srcset') else None) or
                          (img.get('data-srcset', '').split(',')[0].split()[0] if img.get('data-srcset') else None))

                    if src and len(src) > 0:
                        # Convert relative URLs to absolute
                        if src.startswith('//'):
                            src = 'https:' + src
                        elif src.startswith('/'):
                            from urllib.parse import urljoin
                            src = urljoin(url, src)

                        # Skip data URLs and very short URLs
                        if not src.startswith('http') or len(src) < 20:
                            continue

                        # Skip unwanted images by keywords in URL
                        skip_keywords = ['icon', 'logo', 'banner', 'sprite', 'badge', 'arrow', 'button',
                                       'gnb', 'menu', 'nav', 'header', 'footer', 'plus_', 'thumbnail',
                                       '_thumb', '-thumb', 'avatar', 'pixel', '1x1', 'spacer', 'placeholder']
                        if any(keyword in src.lower() for keyword in skip_keywords):
                            continue

                        # Skip very small images based on dimensions in HTML
                        width = img.get('width', '0')
                        height = img.get('height', '0')
                        try:
                            if width and width != '0' and int(width) < 100:
                                continue
                            if height and height != '0' and int(height) < 100:
                                continue
                        except (ValueError, TypeError):
                            pass

                        image_urls.append(src)

                print(f"Scraped {len(image_urls)} images from {url}")

        except Exception as e:
            print(f"Failed to scrape {url}: {e}")

        return image_urls

    def search_product_images(self, product_name: str) -> List[str]:
        """
        Search for product images by scraping official product pages and marketplaces.

        Args:
            product_name: Name of the product to search images for

        Returns:
            List of image URLs
        """
        image_urls = []

        try:
            # Get product pages from Gemini (includes official sites + marketplaces)
            print(f"Getting product pages for '{product_name}'...")
            product_pages = self.get_official_product_pages(product_name)

            # Scrape images from each page
            for page_url in product_pages:
                page_images = self.scrape_images_from_page(page_url)

                # For marketplaces, take more images as they usually have multiple views
                if any(marketplace in page_url.lower() for marketplace in ['amazon', 'flipkart', 'snapdeal', 'croma']):
                    image_urls.extend(page_images[:5])  # Up to 5 images from marketplaces
                else:
                    image_urls.extend(page_images[:3])  # Up to 3 images from official sites

                if len(image_urls) >= 8:  # Collect up to 8 images total
                    break

            # Deduplicate and limit
            image_urls = list(dict.fromkeys(image_urls))[:5]  # Final limit: 5 images

            print(f"Found {len(image_urls)} total image URLs for '{product_name}'")

        except Exception as e:
            print(f"Image search failed: {e}")

        return image_urls[:5]  # Return max 5 images

    def enrich_product_from_web(self, product_name: str, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich product data by fetching information from the web using Gemini.

        Args:
            product_name: Name of the product to search for
            extracted_data: Already extracted product data

        Returns:
            Dict containing enriched product data with web information
        """
        try:
            # Use Gemini with grounding to search the web for product information
            search_prompt = f"""
            Search the web for product information about: "{product_name}"

            IMPORTANT: Prioritize information from MARKETPLACE listings (Amazon India, Flipkart, Snapdeal, Croma, etc.)
            over official brand/company websites. We need PRODUCT-SPECIFIC descriptions, not company/brand descriptions.

            Return a JSON object with the following structure (no markdown, no code blocks):
            {{
                "detailed_description": "Product-specific description focusing on THIS specific product model/variant, what it is, what it does, key specs. NOT company history or brand description. Extract from marketplace product pages.",
                "common_uses": ["use1", "use2"],
                "typical_price_range": "current market price range in INR from marketplaces",
                "popular_brands": ["brand1", "brand2"],
                "key_features": ["specific feature1 of THIS product", "feature2", "feature3"],
                "related_products": ["similar product1", "similar product2"],
                "image_urls": [],
                "sources": ["marketplace1", "marketplace2"]
            }}

            Focus on:
            1. Product-specific descriptions from marketplace listings (Amazon, Flipkart, etc.)
            2. Actual product specifications and features
            3. Current market pricing from e-commerce sites
            4. What the product IS and DOES, not who makes it or company history

            AVOID:
            - Company descriptions or brand history
            - Generic category information
            - Marketing jargon without specific details

            Return ONLY the JSON object, nothing else.
            """

            start_time = time.time()

            # Use Gemini with Google Search grounding enabled
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=search_prompt,
                config=genai.types.GenerateContentConfig(
                    tools=[genai.types.Tool(google_search=genai.types.GoogleSearch())]
                )
            )

            processing_time = time.time() - start_time

            # Extract JSON from response
            result_text = response.text.strip()

            # Remove markdown code blocks if present
            if result_text.startswith('```'):
                result_text = result_text.split('```')[1]
                if result_text.startswith('json'):
                    result_text = result_text[4:].strip()

            web_data = json.loads(result_text)

            # Search for product images separately using web scraping
            print(f"Searching for images of '{product_name}'...")
            image_urls = self.search_product_images(product_name)

            # Merge web data with extracted data
            enriched_data = extracted_data.copy()

            # Enhance description if web has better info
            if web_data.get('detailed_description') and len(web_data['detailed_description']) > len(enriched_data.get('description', '')):
                enriched_data['description'] = web_data['detailed_description']

            # Add web metadata
            enriched_data['web_enrichment'] = {
                'common_uses': web_data.get('common_uses', []),
                'typical_price_range': web_data.get('typical_price_range'),
                'popular_brands': web_data.get('popular_brands', []),
                'key_features': web_data.get('key_features', []),
                'related_products': web_data.get('related_products', []),
                'image_urls': image_urls,  # Use scraped image URLs
                'sources': web_data.get('sources', []),
                'enriched_at': time.time(),
                'processing_time': processing_time
            }

            return {
                'success': True,
                'data': enriched_data,
                'web_data': web_data,
                'processing_time': processing_time
            }

        except Exception as e:
            print(f"Web enrichment failed: {e}")
            # Return original data if enrichment fails
            return {
                'success': False,
                'data': extracted_data,
                'error': str(e),
                'processing_time': 0
            }

    def download_product_images(self, image_urls: List[str], product_name: str) -> List[str]:
        """
        Download product images from URLs.

        Args:
            image_urls: List of image URLs to download
            product_name: Product name for naming the files

        Returns:
            List of local file paths for downloaded images
        """
        downloaded_images = []

        # Create directory for product images if it doesn't exist
        from django.conf import settings
        import os

        media_root = settings.MEDIA_ROOT
        product_images_dir = os.path.join(media_root, 'products', 'web_images')
        os.makedirs(product_images_dir, exist_ok=True)

        for idx, url in enumerate(image_urls[:3]):  # Limit to 3 images
            try:
                response = requests.get(url, timeout=10, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })

                if response.status_code == 200:
                    # Generate filename
                    safe_name = "".join(c for c in product_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
                    safe_name = safe_name.replace(' ', '_')[:50]
                    filename = f"{safe_name}_{idx}_{int(time.time())}.jpg"
                    filepath = os.path.join(product_images_dir, filename)

                    # Save image
                    with open(filepath, 'wb') as f:
                        f.write(response.content)

                    # Return relative path for database storage
                    relative_path = os.path.join('products', 'web_images', filename)
                    downloaded_images.append(relative_path)

            except Exception as e:
                print(f"Failed to download image {url}: {e}")
                continue

        return downloaded_images
