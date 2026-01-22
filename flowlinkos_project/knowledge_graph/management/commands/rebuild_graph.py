"""
Django management command to rebuild a user's knowledge graph.
Clears existing graph and rebuilds from scratch.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from knowledge_graph.models import Entity, Relationship, EntityItemLink, Graph
from knowledge_graph.tasks import rebuild_graph_for_user, batch_index_items
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Rebuild knowledge graph for a user'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'user_id',
            type=int,
            help='ID of the user to rebuild graph for'
        )
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Skip confirmation prompt'
        )
        parser.add_argument(
            '--keep-data',
            action='store_true',
            help='Keep existing data (additive rebuild)'
        )
    
    def handle(self, *args, **options):
        user_id = options['user_id']
        confirm = options.get('confirm', False)
        keep_data = options.get('keep_data', False)
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User with ID {user_id} not found'))
            return
        
        if not keep_data:
            if not confirm:
                self.stdout.write(
                    self.style.WARNING(
                        f'This will DELETE all graph data for {user.username}. Continue? (y/N) '
                    ),
                    ending=''
                )
                response = input()
                if response.lower() != 'y':
                    self.stdout.write(self.style.ERROR('Cancelled'))
                    return
            
            # Clear existing data
            self.stdout.write('Clearing existing graph data...')
            
            entity_count = Entity.objects.filter(user=user).count()
            rel_count = Relationship.objects.filter(user=user).count()
            link_count = EntityItemLink.objects.filter(entity__user=user).count()
            
            Entity.objects.filter(user=user).delete()
            Relationship.objects.filter(user=user).delete()
            EntityItemLink.objects.filter(entity__user=user).delete()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Deleted {entity_count} entities, {rel_count} relationships, {link_count} links'
                )
            )
        
        # Start rebuild
        self.stdout.write('Starting graph rebuild...')
        task = rebuild_graph_for_user.delay(user_id)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Graph rebuild started for {user.username} (Task ID: {task.id})'
            )
        )
        self.stdout.write(
            'Use the Celery task ID above to monitor progress with: celery -A flowlinkos inspect active'
        )
