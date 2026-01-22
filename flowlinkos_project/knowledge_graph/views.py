"""
API views for knowledge graph querying and management.
"""

import logging
from typing import List, Dict, Tuple, Optional
from collections import deque

from django.db.models import Q, Count, Avg, F
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import viewsets, status, filters, pagination
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import JSONParser
from django_filters.rest_framework import DjangoFilterBackend

from knowledge_graph.models import Entity, Relationship, EntityItemLink, Graph, SmartCollection, ClusterItem
from knowledge_graph.serializers import (
    EntitySerializer,
    EntityDetailSerializer,
    RelationshipSerializer,
    EntityItemLinkSerializer,
    GraphSerializer,
    GraphStatsSerializer,
    EntitySearchSerializer,
    RelationshipQuerySerializer,
    PathQuerySerializer,
    PathResponseSerializer,
    SimilarEntitySerializer,
    BatchOperationSerializer,
    SmartCollectionSerializer,
    SmartCollectionDetailSerializer,
    ClusterItemSerializer,
    MergeCollectionsSerializer,
    RenameCollectionSerializer,
    SmartCollectionStatsSerializer,
    CollectionRebuildSerializer,
)
from knowledge_graph.embeddings import get_embedding_service
from knowledge_graph.tasks import (
    index_item_in_graph,
    batch_index_items,
    update_graph_snapshot,
    rebuild_graph_for_user,
    ingest_from_source,
)

logger = logging.getLogger(__name__)


class StandardResultsSetPagination(pagination.PageNumberPagination):
    """Standard pagination for API responses."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class EntityViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing entities in the knowledge graph.
    Provides CRUD operations and advanced querying.
    """
    serializer_class = EntitySerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['entity_type']
    search_fields = ['name', 'description']
    ordering_fields = ['frequency_score', 'created_at', '-frequency_score']
    ordering = ['-frequency_score']
    
    def get_queryset(self):
        """Filter entities by current user."""
        return Entity.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        """Use detailed serializer for retrieve action."""
        if self.action == 'retrieve':
            return EntityDetailSerializer
        return EntitySerializer
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Search entities by name, type, and other criteria.
        
        Query params:
        - q: Search query
        - entity_type: Filter by entity type
        - min_frequency: Minimum frequency score
        """
        queryset = self.get_queryset()
        
        # Text search
        search_query = request.query_params.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        # Entity type filter
        entity_type = request.query_params.get('entity_type')
        if entity_type:
            queryset = queryset.filter(entity_type=entity_type)
        
        # Frequency filter
        min_frequency = request.query_params.get('min_frequency')
        if min_frequency:
            try:
                queryset = queryset.filter(frequency_score__gte=int(min_frequency))
            except ValueError:
                pass
        
        queryset = queryset.order_by('-frequency_score')
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = EntitySearchSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = EntitySearchSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def similar(self, request, pk=None):
        """
        Find similar entities based on semantic similarity.
        
        Query params:
        - top_k: Number of results (default: 5)
        - threshold: Minimum similarity score (0-1, default: 0.6)
        """
        entity = self.get_object()
        
        top_k = int(request.query_params.get('top_k', 5))
        threshold = float(request.query_params.get('threshold', 0.6))
        
        try:
            if not entity.embedding:
                return Response(
                    {'error': 'Entity has no embedding'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get all entities with embeddings
            other_entities = Entity.objects.filter(
                user=request.user,
                embedding__isnull=False
            ).exclude(id=entity.id)
            
            # Compute similarities
            embedding_service = get_embedding_service()
            similarities = []
            
            for other in other_entities:
                score = embedding_service.compute_similarity(
                    entity.embedding,
                    other.embedding
                )
                if score >= threshold:
                    similarities.append((other, score))
            
            # Sort and limit
            similarities.sort(key=lambda x: x[1], reverse=True)
            similar_entities = similarities[:top_k]
            
            result = [
                {
                    'entity_id': e.id,
                    'entity_name': e.name,
                    'entity_type': e.get_entity_type_display(),
                    'similarity_score': round(score, 4)
                }
                for e, score in similar_entities
            ]
            
            return Response(result)
        
        except Exception as e:
            logger.error(f"Error finding similar entities: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def connections(self, request, pk=None):
        """Get all connections (relationships) for an entity."""
        entity = self.get_object()
        
        depth = int(request.query_params.get('depth', 1))
        depth = min(depth, 3)  # Limit depth
        
        connections = self._get_connections(entity, depth)
        
        return Response({
            'entity_id': entity.id,
            'entity_name': entity.name,
            'connections': connections
        })
    
    def _get_connections(self, entity: Entity, depth: int, visited: set = None) -> List[Dict]:
        """Recursively get entity connections."""
        if visited is None:
            visited = set()
        
        if depth <= 0 or entity.id in visited:
            return []
        
        visited.add(entity.id)
        connections = []
        
        # Get outgoing relationships
        outgoing = entity.outgoing_relationships.all()
        for rel in outgoing:
            connections.append({
                'type': 'outgoing',
                'relationship_type': rel.get_relationship_type_display(),
                'target_entity_id': rel.target_entity.id,
                'target_entity_name': rel.target_entity.name,
                'strength': rel.strength,
                'depth': 1
            })
            
            # Recurse
            if depth > 1:
                nested = self._get_connections(rel.target_entity, depth - 1, visited)
                for nested_conn in nested:
                    nested_conn['depth'] = nested_conn.get('depth', 0) + 1
                    connections.append(nested_conn)
        
        # Get incoming relationships
        incoming = entity.incoming_relationships.all()
        for rel in incoming:
            connections.append({
                'type': 'incoming',
                'relationship_type': rel.get_relationship_type_display(),
                'source_entity_id': rel.source_entity.id,
                'source_entity_name': rel.source_entity.name,
                'strength': rel.strength,
                'depth': 1
            })
        
        return connections
    
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
    """ViewSet for managing relationships in the knowledge graph."""
    serializer_class = RelationshipSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['relationship_type']
    ordering_fields = ['strength', 'created_at', '-strength']
    ordering = ['-strength']
    
    def get_queryset(self):
        """Filter relationships by current user."""
        return Relationship.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def query(self, request):
        """
        Query relationships with various filters.
        
        POST body:
        {
            "entity_id": int,
            "relationship_type": string,
            "depth": int (1-5)
        }
        """
        serializer = RelationshipQuerySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        queryset = self.get_queryset()
        
        entity_id = serializer.validated_data.get('entity_id')
        entity_name = serializer.validated_data.get('entity_name')
        rel_type = serializer.validated_data.get('relationship_type')
        
        if entity_id:
            queryset = queryset.filter(
                Q(source_entity_id=entity_id) |
                Q(target_entity_id=entity_id)
            )
        elif entity_name:
            queryset = queryset.filter(
                Q(source_entity__name__icontains=entity_name) |
                Q(target_entity__name__icontains=entity_name)
            )
        
        if rel_type:
            queryset = queryset.filter(relationship_type=rel_type)
        
        queryset = queryset.order_by('-strength')
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = RelationshipSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = RelationshipSerializer(queryset, many=True)
        return Response(serializer.data)


class EntityItemLinkViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing entity-item links."""
    serializer_class = EntityItemLinkSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """Filter links where entity belongs to current user."""
        return EntityItemLink.objects.filter(entity__user=self.request.user)


class GraphViewSet(viewsets.ModelViewSet):
    """ViewSet for managing knowledge graphs."""
    serializer_class = GraphSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter graphs by current user."""
        return Graph.objects.filter(user=self.request.user)
    
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
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get overall graph statistics for the current user.
        """
        user = request.user
        
        entities = Entity.objects.filter(user=user)
        relationships = Relationship.objects.filter(user=user)
        
        total_entities = entities.count()
        total_relationships = relationships.count()
        
        # Calculate average connections
        avg_connections = 0
        if total_entities > 0:
            avg_connections = total_relationships / total_entities
        
        # Get top entities
        top_entities = entities.order_by('-frequency_score')[:10].values(
            'id', 'name', 'entity_type', 'frequency_score'
        )
        
        # Get graph health score
        graph = Graph.objects.filter(user=user, name='Main Knowledge Graph').first()
        health_score = graph.health_score if graph else 0.0
        
        stats = {
            'total_entities': total_entities,
            'total_relationships': total_relationships,
            'average_connections_per_entity': round(avg_connections, 2),
            'top_entities': list(top_entities),
            'health_score': health_score,
            'last_updated': graph.last_indexed if graph else None
        }
        
        serializer = GraphStatsSerializer(stats)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def operations(self, request):
        """
        Perform batch operations on the graph.
        
        POST body:
        {
            "operation": "index_items|rebuild_graph|update_snapshot|cleanup",
            "item_ids": [1, 2, 3],
            "source_type": "notes"
        }
        """
        serializer = BatchOperationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        operation = serializer.validated_data.get('operation')
        item_ids = serializer.validated_data.get('item_ids')
        source_type = serializer.validated_data.get('source_type')
        
        try:
            if operation == 'index_items':
                if item_ids:
                    task = batch_index_items.delay(request.user.id, item_ids)
                else:
                    task = batch_index_items.delay(request.user.id)
                return Response({
                    'success': True,
                    'message': 'Batch indexing started',
                    'task_id': task.id
                })
            
            elif operation == 'rebuild_graph':
                task = rebuild_graph_for_user.delay(request.user.id)
                return Response({
                    'success': True,
                    'message': 'Graph rebuild started',
                    'task_id': task.id
                })
            
            elif operation == 'update_snapshot':
                task = update_graph_snapshot.delay(request.user.id)
                return Response({
                    'success': True,
                    'message': 'Graph snapshot update started',
                    'task_id': task.id
                })
            
            elif operation == 'cleanup':
                task = ingest_from_source.delay(request.user.id, source_type)
                return Response({
                    'success': True,
                    'message': 'Cleanup operation started',
                    'task_id': task.id
                })
            
            else:
                return Response(
                    {'error': 'Unknown operation'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        except Exception as e:
            logger.error(f"Error in graph operation: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def find_path(self, request):
        """
        Find shortest path between two entities.
        
        POST body:
        {
            "source_entity_id": int,
            "target_entity_id": int,
            "max_hops": int
        }
        """
        serializer = PathQuerySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        source_id = serializer.validated_data.get('source_entity_id')
        target_id = serializer.validated_data.get('target_entity_id')
        source_name = serializer.validated_data.get('source_entity_name')
        target_name = serializer.validated_data.get('target_entity_name')
        max_hops = serializer.validated_data.get('max_hops', 3)
        
        try:
            # Resolve entity IDs if names provided
            if source_name and not source_id:
                source = Entity.objects.filter(
                    user=request.user,
                    name__icontains=source_name
                ).first()
                source_id = source.id if source else None
            
            if target_name and not target_id:
                target = Entity.objects.filter(
                    user=request.user,
                    name__icontains=target_name
                ).first()
                target_id = target.id if target else None
            
            if not source_id or not target_id:
                return Response(
                    {'error': 'Source or target entity not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            path, relationships = self._find_shortest_path(
                source_id, target_id, max_hops, request.user
            )
            
            if not path:
                return Response(
                    {'path': [], 'hops': 0, 'found': False},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            result = {
                'path': path,
                'hops': len(path) - 1,
                'found': True,
                'relationships': relationships
            }
            
            return Response(result)
        
        except Exception as e:
            logger.error(f"Error finding path: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _find_shortest_path(
        self,
        source_id: int,
        target_id: int,
        max_hops: int,
        user
    ) -> Tuple[List[Dict], List[Dict]]:
        """BFS to find shortest path between entities."""
        queue = deque([(source_id, [source_id])])
        visited = {source_id}
        relationships = []
        
        while queue:
            current_id, path = queue.popleft()
            
            if len(path) - 1 > max_hops:
                continue
            
            if current_id == target_id:
                # Build response with entity details
                entity_details = []
                for entity_id in path:
                    entity = Entity.objects.get(id=entity_id)
                    entity_details.append({
                        'id': entity.id,
                        'name': entity.name,
                        'type': entity.get_entity_type_display()
                    })
                
                # Get relationships in path
                for i in range(len(path) - 1):
                    rel = Relationship.objects.filter(
                        source_entity_id=path[i],
                        target_entity_id=path[i + 1]
                    ).first()
                    if rel:
                        relationships.append({
                            'from': rel.source_entity.name,
                            'to': rel.target_entity.name,
                            'type': rel.get_relationship_type_display(),
                            'strength': rel.strength
                        })
                
                return entity_details, relationships
            
            # Explore neighbors
            neighbors = Relationship.objects.filter(
                source_entity_id=current_id
            ).values_list('target_entity_id', flat=True)
            
            for neighbor_id in neighbors:
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    queue.append((neighbor_id, path + [neighbor_id]))
        
        return [], []
    
    @action(detail=False, methods=['post'])
    def rebuild_graph(self, request):
        """Rebuild the knowledge graph from items."""
        try:
            task = rebuild_graph_for_user.delay(request.user.id)
            return Response({
                'status': 'Rebuild initiated',
                'message': 'Knowledge graph rebuild started in background',
                'task_id': task.id
            })
        except Exception as e:
            logger.error(f"Error rebuilding graph: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class SmartCollectionViewSet(viewsets.ModelViewSet):
    """ViewSet for smart collections (auto-organization of items)."""
    serializer_class = SmartCollectionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['confidence_score', 'item_count', '-confidence_score']
    ordering = ['-confidence_score']
    
    def get_queryset(self):
        """Filter collections by current user."""
        return SmartCollection.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        """Use detailed serializer for retrieve action."""
        if self.action == 'retrieve':
            return SmartCollectionDetailSerializer
        elif self.action == 'merge':
            return MergeCollectionsSerializer
        elif self.action == 'rename':
            return RenameCollectionSerializer
        elif self.action == 'rebuild':
            return CollectionRebuildSerializer
        elif self.action == 'statistics':
            return SmartCollectionStatsSerializer
        return SmartCollectionSerializer
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get statistics about user's smart collections.
        """
        collections = self.get_queryset()
        total_collections = collections.count()
        
        if total_collections == 0:
            return Response({
                'total_collections': 0,
                'avg_confidence_score': 0.0,
                'avg_items_per_collection': 0.0,
                'categories_breakdown': {},
                'top_collections': [],
                'total_items_organized': 0,
            })
        
        # Calculate stats
        from django.db.models import Avg
        avg_confidence = collections.aggregate(Avg('confidence_score'))['confidence_score__avg'] or 0.0
        avg_items = collections.aggregate(Avg('item_count'))['item_count__avg'] or 0.0
        
        # Category breakdown
        category_counts = {}
        for coll in collections:
            cat = coll.get_category_display()
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        # Top collections by confidence
        top_collections = collections.order_by('-confidence_score')[:5].values(
            'id', 'name', 'confidence_score', 'item_count', 'category'
        )
        
        total_items_organized = ClusterItem.objects.filter(
            collection__user=request.user
        ).count()
        
        stats = {
            'total_collections': total_collections,
            'avg_confidence_score': round(avg_confidence, 2),
            'avg_items_per_collection': round(avg_items, 2),
            'categories_breakdown': category_counts,
            'top_collections': list(top_collections),
            'total_items_organized': total_items_organized,
        }
        
        return Response(stats)
    
    @action(detail=True, methods=['post'])
    def rename(self, request, pk=None):
        """
        Rename a smart collection.
        
        POST body:
        {
            "new_name": string,
            "new_description": string (optional)
        }
        """
        collection = self.get_object()
        serializer = RenameCollectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        collection.name = serializer.validated_data['new_name']
        if 'new_description' in serializer.validated_data:
            collection.description = serializer.validated_data.get('new_description', '')
        collection.is_custom = True  # Mark as customized
        collection.save()
        
        return Response({
            'success': True,
            'message': f"Collection renamed to '{collection.name}'",
            'collection': SmartCollectionSerializer(collection).data
        })
    
    @action(detail=False, methods=['post'])
    def merge(self, request):
        """
        Merge two smart collections.
        
        POST body:
        {
            "source_collection_id": int,
            "target_collection_id": int,
            "new_name": string
        }
        """
        serializer = MergeCollectionsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        source_id = serializer.validated_data['source_collection_id']
        target_id = serializer.validated_data['target_collection_id']
        new_name = serializer.validated_data['new_name']
        
        try:
            source = SmartCollection.objects.get(id=source_id, user=request.user)
            target = SmartCollection.objects.get(id=target_id, user=request.user)
            
            # Move all items from source to target
            source_items = ClusterItem.objects.filter(collection=source)
            for item in source_items:
                ClusterItem.objects.update_or_create(
                    collection=target,
                    item=item.item,
                    defaults={'relationship_strength': item.relationship_strength}
                )
            
            # Update target collection
            target.name = new_name
            target.item_count = target.items.count()
            target.is_custom = True
            target.save()
            
            # Delete source collection
            source.delete()
            
            return Response({
                'success': True,
                'message': f"Collections merged into '{new_name}'",
                'collection': SmartCollectionDetailSerializer(target).data
            })
        
        except SmartCollection.DoesNotExist:
            return Response(
                {'error': 'One or both collections not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error merging collections: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def rebuild(self, request):
        """
        Rebuild smart collections using clustering algorithm.
        
        POST body:
        {
            "algorithm": "kmeans|hdbscan|hierarchical",
            "force_rebuild": boolean,
            "min_items": int
        }
        """
        serializer = CollectionRebuildSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            from knowledge_graph.clustering import cluster_items_for_user
            from knowledge_graph.tasks import refresh_auto_clusters
            
            # Trigger background clustering task
            task = refresh_auto_clusters.delay(
                request.user.id,
                serializer.validated_data.get('algorithm', 'kmeans'),
                serializer.validated_data.get('force_rebuild', False)
            )
            
            return Response({
                'success': True,
                'message': 'Collection rebuild started in background',
                'task_id': task.id
            })
        
        except Exception as e:
            logger.error(f"Error rebuilding collections: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['delete'])
    def remove_item(self, request, pk=None):
        """
        Remove an item from a smart collection.
        
        Query params:
        ?item_id=int
        """
        collection = self.get_object()
        item_id = request.query_params.get('item_id')
        
        if not item_id:
            return Response(
                {'error': 'item_id parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            cluster_item = ClusterItem.objects.get(
                collection=collection,
                item_id=item_id
            )
            cluster_item.delete()
            collection.item_count = collection.items.count()
            collection.save()
            
            return Response({
                'success': True,
                'message': 'Item removed from collection'
            })
        
        except ClusterItem.DoesNotExist:
            return Response(
                {'error': 'Item not found in collection'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['post'])
    def add_item(self, request):
        """
        Add an item to a smart collection.
        
        POST body:
        {
            "collection_id": int,
            "item_id": int,
            "relationship_strength": float (0-1, optional)
        }
        """
        collection_id = request.data.get('collection_id')
        item_id = request.data.get('item_id')
        strength = float(request.data.get('relationship_strength', 0.8))
        
        try:
            collection = SmartCollection.objects.get(id=collection_id, user=request.user)
            from api.models import Item
            item = Item.objects.get(id=item_id, user=request.user)
            
            cluster_item, created = ClusterItem.objects.update_or_create(
                collection=collection,
                item=item,
                defaults={'relationship_strength': max(0.0, min(1.0, strength))}
            )
            
            collection.item_count = collection.items.count()
            collection.save()
            
            return Response({
                'success': True,
                'message': 'Item added to collection',
                'cluster_item': ClusterItemSerializer(cluster_item).data
            })
        
        except (SmartCollection.DoesNotExist, Exception) as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )