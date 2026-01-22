from django.db import models
from django.contrib.auth.models import User
from core.models import BaseModel
from api.models import Item


class Entity(BaseModel):
    """Represents an entity in the knowledge graph (concept, person, place, etc)."""
    ENTITY_TYPES = [
        ('concept', 'Concept'),
        ('person', 'Person'),
        ('place', 'Place'),
        ('organization', 'Organization'),
        ('project', 'Project'),
        ('topic', 'Topic'),
        ('other', 'Other'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='entities')
    name = models.CharField(max_length=500)
    entity_type = models.CharField(max_length=50, choices=ENTITY_TYPES)
    description = models.TextField(blank=True)
    embedding = models.JSONField(blank=True, null=True)  # Vector representation
    metadata = models.JSONField(default=dict, blank=True)
    frequency_score = models.IntegerField(default=0)  # How often mentioned
    
    def __str__(self):
        return f"{self.name} ({self.get_entity_type_display()})"
    
    class Meta:
        verbose_name = 'Entity'
        verbose_name_plural = 'Entities'
        ordering = ['-frequency_score', '-created_at']
        unique_together = ('user', 'name', 'entity_type')


class Relationship(BaseModel):
    """Represents a relationship between entities in the knowledge graph."""
    RELATIONSHIP_TYPES = [
        ('mentions', 'Mentions'),
        ('related_to', 'Related To'),
        ('depends_on', 'Depends On'),
        ('part_of', 'Part Of'),
        ('similar_to', 'Similar To'),
        ('created_by', 'Created By'),
        ('assigned_to', 'Assigned To'),
        ('references', 'References'),
        ('custom', 'Custom'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='relationships')
    source_entity = models.ForeignKey(Entity, on_delete=models.CASCADE, related_name='outgoing_relationships')
    target_entity = models.ForeignKey(Entity, on_delete=models.CASCADE, related_name='incoming_relationships')
    relationship_type = models.CharField(max_length=50, choices=RELATIONSHIP_TYPES)
    strength = models.FloatField(default=1.0)  # 0-1 strength of relationship
    metadata = models.JSONField(default=dict, blank=True)
    
    def __str__(self):
        return f"{self.source_entity.name} -> {self.relationship_type} -> {self.target_entity.name}"
    
    class Meta:
        verbose_name = 'Relationship'
        verbose_name_plural = 'Relationships'
        ordering = ['-strength', '-created_at']
        unique_together = ('source_entity', 'target_entity', 'relationship_type')


class EntityItemLink(BaseModel):
    """Links entities to items they appear in."""
    entity = models.ForeignKey(Entity, on_delete=models.CASCADE, related_name='item_links')
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='entity_links')
    mention_count = models.IntegerField(default=1)
    context = models.TextField(blank=True)  # Context of mention
    
    def __str__(self):
        return f"{self.entity.name} in {self.item.title}"
    
    class Meta:
        verbose_name = 'Entity Item Link'
        verbose_name_plural = 'Entity Item Links'
        unique_together = ('entity', 'item')


class Graph(BaseModel):
    """Represents a snapshot of the knowledge graph."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='graphs')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    entity_count = models.IntegerField(default=0)
    relationship_count = models.IntegerField(default=0)
    last_indexed = models.DateTimeField(auto_now=True)
    health_score = models.FloatField(default=1.0)  # 0-1 graph health
    
    def __str__(self):
        return f"{self.user.username}'s Knowledge Graph: {self.name}"
    
    class Meta:
        verbose_name = 'Knowledge Graph'
        verbose_name_plural = 'Knowledge Graphs'
        ordering = ['-created_at']


class SmartCollection(BaseModel):
    """Auto-generated collection of related items based on clustering."""
    COLLECTION_CATEGORIES = [
        ('project', 'Project'),
        ('topic', 'Topic'),
        ('timeline', 'Timeline'),
        ('theme', 'Theme'),
        ('custom', 'Custom'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='smart_collections')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, choices=COLLECTION_CATEGORIES, default='custom')
    confidence_score = models.FloatField(default=0.0)  # 0-1 confidence in this clustering
    item_count = models.IntegerField(default=0)
    
    # Clustering metadata
    cluster_id = models.IntegerField(null=True, blank=True)  # ID from clustering algorithm
    algorithm = models.CharField(
        max_length=50,
        choices=[('kmeans', 'K-Means'), ('hdbscan', 'HDBSCAN'), ('hierarchical', 'Hierarchical')],
        default='kmeans'
    )
    last_updated = models.DateTimeField(auto_now=True)
    
    # User customization
    is_custom = models.BooleanField(default=False)  # User-created vs auto-generated
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"
    
    class Meta:
        verbose_name = 'Smart Collection'
        verbose_name_plural = 'Smart Collections'
        ordering = ['-confidence_score', '-created_at']
        unique_together = ('user', 'name')


class ClusterItem(BaseModel):
    """Maps items to their smart collections."""
    collection = models.ForeignKey(SmartCollection, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='clusters')
    relationship_strength = models.FloatField(default=1.0)  # 0-1 strength of connection to cluster
    
    def __str__(self):
        return f"{self.item.title} -> {self.collection.name}"
    
    class Meta:
        verbose_name = 'Cluster Item'
        verbose_name_plural = 'Cluster Items'
        unique_together = ('collection', 'item')
