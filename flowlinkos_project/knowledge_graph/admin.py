from django.contrib import admin
from .models import Entity, Relationship, EntityItemLink, Graph


@admin.register(Entity)
class EntityAdmin(admin.ModelAdmin):
    list_display = ('name', 'entity_type', 'user', 'frequency_score', 'created_at')
    list_filter = ('entity_type', 'created_at')
    search_fields = ('name', 'user__username')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Relationship)
class RelationshipAdmin(admin.ModelAdmin):
    list_display = ('source_entity', 'relationship_type', 'target_entity', 'strength', 'created_at')
    list_filter = ('relationship_type', 'strength', 'created_at')
    search_fields = ('source_entity__name', 'target_entity__name', 'user__username')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(EntityItemLink)
class EntityItemLinkAdmin(admin.ModelAdmin):
    list_display = ('entity', 'item', 'mention_count', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('entity__name', 'item__title')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Graph)
class GraphAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'entity_count', 'relationship_count', 'health_score', 'created_at')
    list_filter = ('health_score', 'created_at')
    search_fields = ('name', 'user__username')
    readonly_fields = ('created_at', 'updated_at')
