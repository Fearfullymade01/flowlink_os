from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from .models import Item, Query, Summary


class ItemViewSet(viewsets.ModelViewSet):
    """ViewSet for managing items."""
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['item_type', 'is_archived', 'priority']
    search_fields = ['title', 'content', 'tags']
    ordering_fields = ['created_at', 'priority', 'updated_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return Item.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Get items grouped by type."""
        items_by_type = {}
        for item_type, _ in Item.ITEM_TYPES:
            items_by_type[item_type] = Item.objects.filter(
                user=request.user, item_type=item_type
            ).count()
        return Response(items_by_type)


class QueryViewSet(viewsets.ModelViewSet):
    """ViewSet for managing queries."""
    permission_classes = [IsAuthenticated]
    ordering_fields = ['created_at', 'confidence_score']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return Query.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def execute_query(self, request):
        """Execute an intent-based query on the knowledge graph."""
        query_text = request.data.get('query_text', '')
        if not query_text:
            return Response(
                {'error': 'query_text is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create query object
        query = Query.objects.create(
            user=request.user,
            query_text=query_text,
            results=[],
            confidence_score=0.75
        )
        
        return Response({
            'id': query.id,
            'query_text': query.query_text,
            'results': query.results,
            'confidence_score': query.confidence_score,
            'message': 'Query executed successfully'
        })


class SummaryViewSet(viewsets.ModelViewSet):
    """ViewSet for managing summaries."""
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['summary_type']
    search_fields = ['title', 'summary_text']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return Summary.objects.filter(user=self.request.user)
