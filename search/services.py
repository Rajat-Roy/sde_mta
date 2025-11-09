"""
Search service for multimodal search with vector similarity and geo-location.
"""

import numpy as np
import os
from typing import List, Dict, Any, Optional
from django.db.models import Q
from geopy.distance import geodesic

from products.models import Product
from ai_ingestion.services import GeminiIngestionService
from ai_ingestion.mock_services import MockGeminiService
from .models import SearchQuery, SearchResult


def get_ai_service():
    """
    Get AI service based on USE_MOCK_AI environment variable.
    Returns MockGeminiService for testing or real GeminiIngestionService.
    """
    use_mock = os.getenv('USE_MOCK_AI', 'False').lower() == 'true'
    if use_mock:
        return MockGeminiService()
    else:
        return GeminiIngestionService()


class SearchService:
    """Service for multimodal product search."""

    def __init__(self):
        self.ai_service = get_ai_service()

    def search(
        self,
        query: str,
        search_type: str = 'text',
        user_location: Optional[Dict] = None,
        district_filter: Optional[str] = None,
        category_filter: Optional[str] = None,
        max_distance_km: Optional[float] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Perform multimodal search combining vector similarity and geo-location.

        Args:
            query: Search query text
            search_type: Type of search (text, voice, image)
            user_location: Dict with 'latitude' and 'longitude'
            district_filter: Filter by district
            category_filter: Filter by category
            max_distance_km: Maximum distance in kilometers
            limit: Maximum number of results

        Returns:
            List of product results with scores
        """
        # Generate search embedding
        query_embedding = self.ai_service.generate_search_embedding(query)

        # Build base queryset
        queryset = Product.objects.filter(is_active=True, is_sold=False)

        # Apply filters
        if district_filter:
            queryset = queryset.filter(district=district_filter)

        if category_filter:
            queryset = queryset.filter(category__name=category_filter)

        # Get all products (we'll score them)
        products = list(queryset)

        # Score each product
        scored_products = []
        for product in products:
            score_data = self._score_product(
                product,
                query_embedding,
                user_location,
                max_distance_km
            )

            if score_data:  # Only include if within distance filter
                scored_products.append({
                    'product': product,
                    **score_data
                })

        # Sort by combined score (similarity + distance bonus)
        scored_products.sort(key=lambda x: x['combined_score'], reverse=True)

        # Limit results
        return scored_products[:limit]

    def _score_product(
        self,
        product: Product,
        query_embedding: List[float],
        user_location: Optional[Dict],
        max_distance_km: Optional[float]
    ) -> Optional[Dict[str, Any]]:
        """
        Score a product based on vector similarity and geo-proximity.

        Returns:
            Dict with scores or None if filtered out
        """
        # Calculate similarity score
        similarity_score = 0.0
        if query_embedding and product.embedding:
            similarity_score = self._cosine_similarity(
                query_embedding,
                product.embedding
            )

        # Calculate distance
        distance_km = None
        distance_score = 0.0

        if user_location and product.latitude and product.longitude:
            user_coords = (user_location['latitude'], user_location['longitude'])
            product_coords = (float(product.latitude), float(product.longitude))

            distance_km = geodesic(user_coords, product_coords).kilometers

            # Filter by max distance if specified
            if max_distance_km and distance_km > max_distance_km:
                return None

            # Distance score: closer is better (inverse relationship)
            # Score decreases with distance, but never goes below 0
            if distance_km == 0:
                distance_score = 1.0
            else:
                # Normalize: products within 5km get high scores
                distance_score = max(0, 1.0 - (distance_km / 10.0))

        # Combined score: weighted average
        # 70% similarity, 30% proximity
        combined_score = (0.7 * similarity_score) + (0.3 * distance_score)

        return {
            'similarity_score': similarity_score,
            'distance_km': distance_km,
            'distance_score': distance_score,
            'combined_score': combined_score
        }

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if not vec1 or not vec2:
            return 0.0

        try:
            arr1 = np.array(vec1)
            arr2 = np.array(vec2)

            # Ensure same length
            if len(arr1) != len(arr2):
                return 0.0

            # Calculate cosine similarity
            dot_product = np.dot(arr1, arr2)
            norm1 = np.linalg.norm(arr1)
            norm2 = np.linalg.norm(arr2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            similarity = dot_product / (norm1 * norm2)

            # Normalize to 0-1 range
            return float((similarity + 1) / 2)

        except Exception as e:
            print(f"Error calculating similarity: {e}")
            return 0.0

    def save_search_query(
        self,
        user,
        search_type: str,
        query_text: str,
        results: List[Dict],
        **kwargs
    ) -> SearchQuery:
        """
        Save search query and results for analytics.

        Args:
            user: User performing search
            search_type: Type of search
            query_text: Query text
            results: List of search results
            **kwargs: Additional search parameters

        Returns:
            Created SearchQuery instance
        """
        search_query = SearchQuery.objects.create(
            user=user,
            search_type=search_type,
            query_text=query_text,
            query_embedding=kwargs.get('query_embedding', []),
            district_filter=kwargs.get('district_filter'),
            category_filter=kwargs.get('category_filter'),
            max_distance_km=kwargs.get('max_distance_km'),
            search_latitude=kwargs.get('user_location', {}).get('latitude'),
            search_longitude=kwargs.get('user_location', {}).get('longitude'),
            results_count=len(results)
        )

        # Save individual results
        for idx, result in enumerate(results):
            SearchResult.objects.create(
                search_query=search_query,
                product=result['product'],
                rank_position=idx + 1,
                similarity_score=result['similarity_score'],
                distance_km=result.get('distance_km')
            )

        return search_query
