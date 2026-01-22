"""
Django REST Framework serializers for API endpoints.
"""

from rest_framework import serializers
from .models import Item, Query, Summary


class ItemSerializer(serializers.ModelSerializer):
    """Serializer for Item model."""
    item_type_display = serializers.CharField(source='get_item_type_display', read_only=True)
    source_name = serializers.CharField(source='source.name', read_only=True, allow_null=True)
    
    class Meta:
        model = Item
        fields = [
            'id', 'item_type', 'item_type_display',
            'title', 'content', 'tags', 'metadata',
            'source', 'source_name',
            'is_archived', 'priority',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class QuerySerializer(serializers.ModelSerializer):
    """Serializer for Query model."""
    
    class Meta:
        model = Query
        fields = [
            'id', 'query_text', 'query_embedding',
            'results', 'confidence_score', 'execution_time',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'query_embedding', 'results', 'confidence_score', 'execution_time', 'created_at', 'updated_at']


class SummarySerializer(serializers.ModelSerializer):
    """Serializer for Summary model."""
    source_items = ItemSerializer(many=True, read_only=True)
    source_item_ids = serializers.PrimaryKeyRelatedField(
        queryset=Item.objects.all(),
        many=True,
        write_only=True,
        source='source_items'
    )
    
    class Meta:
        model = Summary
        fields = [
            'id', 'title', 'summary_text', 'summary_type',
            'source_items', 'source_item_ids',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
