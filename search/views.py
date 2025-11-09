from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.shortcuts import render

from .services import SearchService
from products.serializers import ProductListSerializer


def search_view(request):
    """Template view for search."""
    return render(request, 'search/search.html')


class MultimodalSearchView(APIView):
    """API view for multimodal search."""
    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, request):
        """Perform multimodal search."""
        query = request.data.get('query')
        if not query:
            return Response({'error': 'Query is required'}, status=status.HTTP_400_BAD_REQUEST)

        search_type = request.data.get('search_type', 'text')
        district = request.data.get('district')
        category = request.data.get('category')
        max_distance_km = request.data.get('max_distance_km')

        # Get user location
        user_location = None
        if request.data.get('latitude') and request.data.get('longitude'):
            user_location = {
                'latitude': float(request.data['latitude']),
                'longitude': float(request.data['longitude'])
            }

        # Perform search
        search_service = SearchService()
        results = search_service.search(
            query=query,
            search_type=search_type,
            user_location=user_location,
            district_filter=district,
            category_filter=category,
            max_distance_km=float(max_distance_km) if max_distance_km else None
        )

        # Serialize results
        response_data = []
        for result in results:
            product_data = ProductListSerializer(result['product'], context={'request': request}).data
            product_data['search_score'] = result['combined_score']
            product_data['similarity_score'] = result['similarity_score']
            product_data['distance_km'] = result.get('distance_km')
            response_data.append(product_data)

        return Response({'results': response_data, 'count': len(response_data)})
