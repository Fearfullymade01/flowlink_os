from django.contrib import admin
from .models import Item, Query, Summary


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'item_type', 'user', 'priority', 'is_archived', 'created_at')
    list_filter = ('item_type', 'is_archived', 'priority', 'created_at')
    search_fields = ('title', 'content', 'user__username')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Query)
class QueryAdmin(admin.ModelAdmin):
    list_display = ('query_text', 'user', 'confidence_score', 'execution_time', 'created_at')
    list_filter = ('confidence_score', 'created_at')
    search_fields = ('query_text', 'user__username')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Summary)
class SummaryAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'summary_type', 'created_at')
    list_filter = ('summary_type', 'created_at')
    search_fields = ('title', 'user__username')
    readonly_fields = ('created_at', 'updated_at')
