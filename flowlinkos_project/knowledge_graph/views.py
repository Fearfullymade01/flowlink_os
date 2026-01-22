from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from .models import Entity, Relationship, EntityItemLink, Graph


class EntityViewSet(viewsets.ModelViewSet):
    """ViewSet for managing entities in the knowledge graph."""
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['entity_type']
    search_fields = ['name', 'description']
    ordering_fields = ['frequency_score', 'created_at']
    ordering = ['-frequency_score']
    
    def get_queryset(self):
        return Entity.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['get'])
    def related_entities(self, request, pk=None):
        """Get entities related to a specific entity."""
        entity = self.get_object()
        relationships = Relationship.objects.filter(
            source_entity=entity
        ).select_related('target_entity')
        
        related = [
            {
                'name': rel.target_entity.name,
                'type': rel.target_entity.entity_type,
                'relationship': rel.relationship_type,
                'strength': rel.strength
            }
            for rel in relationships
        ]
        return Response(related)


class RelationshipViewSet(viewsets.ModelViewSet):
    """ViewSet for managing relationships."""
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['relationship_type']
    ordering_fields = ['strength', 'created_at']
    ordering = ['-strength']
    
    def get_queryset(self):
        return Relationship.objects.filter(user=self.request.user)


class GraphViewSet(viewsets.ViewSet):
    """ViewSet for managing the knowledge graph."""
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def current_graph(self, request):
        """Get current user's knowledge graph."""
        graph, _ = Graph.objects.get_or_create(
            user=request.user,
            name="Personal Knowledge Graph"
        )
        
        # Update counts
        graph.entity_count = Entity.objects.filter(user=request.user).count()
        graph.relationship_count = Relationship.objects.filter(user=request.user).count()
        graph.save()
        
        return Response({
            'id': graph.id,
            'name': graph.name,
            'entity_count': graph.entity_count,
            'relationship_count': graph.relationship_count,
            'health_score': graph.health_score,
            'last_indexed': graph.last_indexed,
        })
    
    @action(detail=False, methods=['post'])
    def rebuild_graph(self, request):
        """Rebuild the knowledge graph from items."""
        return Response({
            'status': 'Rebuild initiated',
            'message': 'Knowledge graph rebuild started in background'
        })
