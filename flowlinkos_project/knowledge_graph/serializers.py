"""
Django REST Framework serializers for knowledge graph endpoints.
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from knowledge_graph.models import Entity, Relationship, EntityItemLink, Graph, SmartCollection, ClusterItem


class EntitySerializer(serializers.ModelSerializer):
    """Serializer for Entity model."""
    entity_type_display = serializers.CharField(source='get_entity_type_display', read_only=True)
    
    class Meta:
        model = Entity
        fields = [
            'id', 'name', 'entity_type', 'entity_type_display',
            'description', 'embedding', 'metadata',
            'frequency_score', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'embedding', 'frequency_score', 'created_at', 'updated_at']


class RelationshipSerializer(serializers.ModelSerializer):
    """Serializer for Relationship model."""
    source_entity_name = serializers.CharField(source='source_entity.name', read_only=True)
    target_entity_name = serializers.CharField(source='target_entity.name', read_only=True)
    relationship_type_display = serializers.CharField(source='get_relationship_type_display', read_only=True)
    
    class Meta:
        model = Relationship
        fields = [
            'id', 'source_entity', 'source_entity_name',
            'target_entity', 'target_entity_name',
            'relationship_type', 'relationship_type_display',
            'strength', 'metadata',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class EntityItemLinkSerializer(serializers.ModelSerializer):
    """Serializer for EntityItemLink model."""
    entity_name = serializers.CharField(source='entity.name', read_only=True)
    item_title = serializers.CharField(source='item.title', read_only=True)
    
    class Meta:
        model = EntityItemLink
        fields = [
            'id', 'entity', 'entity_name',
            'item', 'item_title',
            'mention_count', 'context',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class GraphSerializer(serializers.ModelSerializer):
    """Serializer for Knowledge Graph model."""
    
    class Meta:
        model = Graph
        fields = [
            'id', 'name', 'description',
            'entity_count', 'relationship_count',
            'health_score', 'last_indexed',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'entity_count', 'relationship_count',
            'health_score', 'last_indexed',
            'created_at', 'updated_at'
        ]


class EntityDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for Entity with relationships."""
    entity_type_display = serializers.CharField(source='get_entity_type_display', read_only=True)
    incoming_relationships = serializers.SerializerMethodField()
    outgoing_relationships = serializers.SerializerMethodField()
    connected_items = serializers.SerializerMethodField()
    
    class Meta:
        model = Entity
        fields = [
            'id', 'name', 'entity_type', 'entity_type_display',
            'description', 'frequency_score',
            'incoming_relationships', 'outgoing_relationships',
            'connected_items', 'metadata',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'frequency_score',
            'created_at', 'updated_at'
        ]
    
    def get_incoming_relationships(self, obj):
        """Get incoming relationships."""
        relationships = obj.incoming_relationships.all()[:10]
        return [
            {
                'source_entity': rel.source_entity.name,
                'relationship_type': rel.get_relationship_type_display(),
                'strength': rel.strength,
                'id': rel.id
            }
            for rel in relationships
        ]
    
    def get_outgoing_relationships(self, obj):
        """Get outgoing relationships."""
        relationships = obj.outgoing_relationships.all()[:10]
        return [
            {
                'target_entity': rel.target_entity.name,
                'relationship_type': rel.get_relationship_type_display(),
                'strength': rel.strength,
                'id': rel.id
            }
            for rel in relationships
        ]
    
    def get_connected_items(self, obj):
        """Get items connected to this entity."""
        links = obj.item_links.all()[:5]
        return [
            {
                'item_id': link.item.id,
                'item_title': link.item.title,
                'item_type': link.item.get_item_type_display(),
                'mention_count': link.mention_count
            }
            for link in links
        ]


class GraphStatsSerializer(serializers.Serializer):
    """Serializer for graph statistics."""
    total_entities = serializers.IntegerField()
    total_relationships = serializers.IntegerField()
    average_connections_per_entity = serializers.FloatField()
    top_entities = serializers.ListField()
    health_score = serializers.FloatField()
    last_updated = serializers.DateTimeField()


class EntitySearchSerializer(serializers.Serializer):
    """Serializer for entity search results."""
    id = serializers.IntegerField()
    name = serializers.CharField()
    entity_type = serializers.CharField()
    frequency_score = serializers.IntegerField()
    similarity_score = serializers.FloatField(required=False)
    description = serializers.CharField(required=False)


class RelationshipQuerySerializer(serializers.Serializer):
    """Serializer for relationship query requests."""
    entity_id = serializers.IntegerField(required=False)
    entity_name = serializers.CharField(required=False, max_length=500)
    relationship_type = serializers.CharField(required=False, max_length=50)
    depth = serializers.IntegerField(default=1, min_value=1, max_value=5)
    include_metadata = serializers.BooleanField(default=False)


class PathQuerySerializer(serializers.Serializer):
    """Serializer for finding paths between entities."""
    source_entity_id = serializers.IntegerField(required=False)
    target_entity_id = serializers.IntegerField(required=False)
    source_entity_name = serializers.CharField(required=False, max_length=500)
    target_entity_name = serializers.CharField(required=False, max_length=500)
    max_hops = serializers.IntegerField(default=3, min_value=1, max_value=10)


class PathResponseSerializer(serializers.Serializer):
    """Serializer for path query responses."""
    path = serializers.ListField()
    hops = serializers.IntegerField()
    strength = serializers.FloatField()
    relationships = serializers.ListField()


class BatchOperationSerializer(serializers.Serializer):
    """Serializer for batch operations."""
    operation = serializers.ChoiceField(
        choices=['index_items', 'rebuild_graph', 'update_snapshot', 'cleanup']
    )
    item_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    source_type = serializers.CharField(required=False, max_length=50)


class SimilarEntitySerializer(serializers.Serializer):
    """Serializer for similar entity results."""
    entity_id = serializers.IntegerField()
    entity_name = serializers.CharField()
    entity_type = serializers.CharField()
    similarity_score = serializers.FloatField()

class ClusterItemSerializer(serializers.ModelSerializer):
    """Serializer for items within a smart collection."""
    item_title = serializers.CharField(source='item.title', read_only=True)
    item_type = serializers.CharField(source='item.get_item_type_display', read_only=True)
    
    class Meta:
        model = ClusterItem
        fields = [
            'id', 'item', 'item_title', 'item_type',
            'relationship_strength', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class SmartCollectionSerializer(serializers.ModelSerializer):
    """Serializer for SmartCollection model."""
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    algorithm_display = serializers.CharField(source='get_algorithm_display', read_only=True)
    
    class Meta:
        model = SmartCollection
        fields = [
            'id', 'name', 'description', 'category', 'category_display',
            'confidence_score', 'item_count', 'algorithm', 'algorithm_display',
            'is_custom', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'confidence_score', 'item_count', 'algorithm',
            'created_at', 'updated_at'
        ]


class SmartCollectionDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for SmartCollection with items."""
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    algorithm_display = serializers.CharField(source='get_algorithm_display', read_only=True)
    items = ClusterItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = SmartCollection
        fields = [
            'id', 'name', 'description', 'category', 'category_display',
            'confidence_score', 'item_count', 'algorithm', 'algorithm_display',
            'is_custom', 'is_active', 'items',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'confidence_score', 'item_count', 'algorithm',
            'created_at', 'updated_at'
        ]


class MergeCollectionsSerializer(serializers.Serializer):
    """Serializer for merging two smart collections."""
    source_collection_id = serializers.IntegerField()
    target_collection_id = serializers.IntegerField()
    new_name = serializers.CharField(max_length=255)
    
    def validate(self, data):
        """Ensure source and target are different."""
        if data['source_collection_id'] == data['target_collection_id']:
            raise serializers.ValidationError("Cannot merge a collection with itself")
        return data


class RenameCollectionSerializer(serializers.Serializer):
    """Serializer for renaming a smart collection."""
    new_name = serializers.CharField(max_length=255)
    new_description = serializers.CharField(required=False, allow_blank=True)


class SmartCollectionStatsSerializer(serializers.Serializer):
    """Serializer for smart collection statistics."""
    total_collections = serializers.IntegerField()
    avg_confidence_score = serializers.FloatField()
    avg_items_per_collection = serializers.FloatField()
    categories_breakdown = serializers.DictField()
    top_collections = serializers.ListField()
    total_items_organized = serializers.IntegerField()


class CollectionRebuildSerializer(serializers.Serializer):
    """Serializer for rebuilding collections."""
    algorithm = serializers.ChoiceField(
        choices=['kmeans', 'hdbscan', 'hierarchical'],
        default='kmeans'
    )
    force_rebuild = serializers.BooleanField(default=False)
    min_items = serializers.IntegerField(default=3, min_value=1)