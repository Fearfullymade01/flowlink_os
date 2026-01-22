"""
Django management command to index items into the knowledge graph.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from api.models import Item
from knowledge_graph.tasks import batch_index_items, index_item_in_graph
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Index items into the knowledge graph'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'user_id',
            type=int,
            help='ID of the user to index items for'
        )
        parser.add_argument(
            '--item-ids',
            type=int,
            nargs='+',
            help='Specific item IDs to index'
        )
        parser.add_argument(
            '--item-type',
            choices=['note', 'file', 'message', 'bookmark', 'task'],
            help='Index only items of this type'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=50,
            help='Batch size for processing'
        )
    
    def handle(self, *args, **options):
        user_id = options['user_id']
        item_ids = options.get('item_ids')
        item_type = options.get('item_type')
        batch_size = options.get('batch_size', 50)
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User with ID {user_id} not found'))
            return
        
        # Build query
        queryset = Item.objects.filter(user=user, is_archived=False)
        
        if item_ids:
            queryset = queryset.filter(id__in=item_ids)
        
        if item_type:
            queryset = queryset.filter(item_type=item_type)
        
        total_items = queryset.count()
        
        if total_items == 0:
            self.stdout.write(self.style.WARNING('No items found to index'))
            return
        
        self.stdout.write(f'Indexing {total_items} items for {user.username}...')
        
        # Process in batches
        if item_ids and len(item_ids) <= batch_size:
            # Small number of items - queue as single batch task
            task = batch_index_items.delay(user_id, item_ids)
            self.stdout.write(
                self.style.SUCCESS(f'Batch indexing queued (Task ID: {task.id})')
            )
        else:
            # Larger number of items - queue multiple batch tasks
            item_ids_list = list(queryset.values_list('id', flat=True))
            
            for i in range(0, len(item_ids_list), batch_size):
                batch = item_ids_list[i:i + batch_size]
                task = batch_index_items.delay(user_id, batch)
                self.stdout.write(f'Queued batch {i // batch_size + 1} (Task ID: {task.id})')
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'All {(len(item_ids_list) // batch_size) + 1} batches queued for processing'
                )
            )
