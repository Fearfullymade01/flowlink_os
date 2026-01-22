from django.db import models
from django.contrib.auth.models import User


class BaseModel(models.Model):
    """Abstract base model with common fields."""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UserProfile(BaseModel):
    """Extended user profile for FlowLinkOS."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    timezone = models.CharField(max_length=50, default='UTC')
    is_verified = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Profile: {self.user.username}"
    
    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
        ordering = ['-created_at']


class Source(BaseModel):
    """Represents a data source (notes, files, messages, bookmarks, tasks)."""
    SOURCE_TYPES = [
        ('notes', 'Notes'),
        ('files', 'Files'),
        ('messages', 'Messages'),
        ('bookmarks', 'Bookmarks'),
        ('tasks', 'Tasks'),
        ('emails', 'Emails'),
        ('other', 'Other'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sources')
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPES)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_source_type_display()})"
    
    class Meta:
        verbose_name = 'Source'
        verbose_name_plural = 'Sources'
        ordering = ['-created_at']
        unique_together = ('user', 'source_type', 'name')


class Workflow(BaseModel):
    """Represents a learned user workflow or pattern."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workflows')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    workflow_data = models.JSONField()
    confidence_score = models.FloatField(default=0.0)  # 0-1 confidence
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.user.username}: {self.name}"
    
    class Meta:
        verbose_name = 'Workflow'
        verbose_name_plural = 'Workflows'
        ordering = ['-confidence_score', '-created_at']
