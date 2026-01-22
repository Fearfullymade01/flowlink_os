from django.db import models
from django.contrib.auth.models import User
from core.models import BaseModel


class Item(BaseModel):
    """Represents an item from any source (note, file, message, bookmark, task)."""
    ITEM_TYPES = [
        ('note', 'Note'),
        ('file', 'File'),
        ('message', 'Message'),
        ('bookmark', 'Bookmark'),
        ('task', 'Task'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='items')
    source = models.ForeignKey('core.Source', on_delete=models.SET_NULL, null=True, related_name='items')
    item_type = models.CharField(max_length=20, choices=ITEM_TYPES)
    title = models.CharField(max_length=500)
    content = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    tags = models.CharField(max_length=500, blank=True)  # Comma-separated
    is_archived = models.BooleanField(default=False)
    priority = models.IntegerField(default=0)  # 0=normal, 1=low, 2=high
    
    def __str__(self):
        return f"{self.get_item_type_display()}: {self.title}"
    
    class Meta:
        verbose_name = 'Item'
        verbose_name_plural = 'Items'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'item_type']),
            models.Index(fields=['user', 'is_archived']),
        ]


class Query(BaseModel):
    """Represents an intent-based query made by the user."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='queries')
    query_text = models.TextField()
    query_embedding = models.JSONField(blank=True, null=True)  # Store vector embedding
    results = models.JSONField(default=list)  # Store result IDs
    confidence_score = models.FloatField(default=0.0)
    execution_time = models.FloatField(default=0.0)  # milliseconds
    
    def __str__(self):
        return f"Query: {self.query_text[:50]}"
    
    class Meta:
        verbose_name = 'Query'
        verbose_name_plural = 'Queries'
        ordering = ['-created_at']


class Summary(BaseModel):
    """Represents an auto-generated summary of items."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='summaries')
    title = models.CharField(max_length=500)
    summary_text = models.TextField()
    source_items = models.ManyToManyField(Item, related_name='summaries')
    summary_type = models.CharField(max_length=50)  # daily, weekly, category, query, etc.
    
    def __str__(self):
        return f"Summary: {self.title}"
    
    class Meta:
        verbose_name = 'Summary'
        verbose_name_plural = 'Summaries'
        ordering = ['-created_at']
