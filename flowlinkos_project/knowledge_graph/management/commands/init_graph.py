"""
Django management command to initialize a user's knowledge graph.
Ingests existing data and builds initial graph structure.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from knowledge_graph.tasks import rebuild_graph_for_user
from knowledge_graph.models import Graph
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Initialize knowledge graph for a user'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'user_id',
            type=int,
            help='ID of the user to initialize graph for'
        )
        parser.add_argument(
            '--async',
            action='store_true',
            help='Run as background Celery task instead of blocking'
        )
    
    def handle(self, *args, **options):
        user_id = options['user_id']
        async_mode = options.get('async', False)
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User with ID {user_id} not found'))
            return
        
        # Create or get default graph
        graph, created = Graph.objects.get_or_create(
            user=user,
            name='Main Knowledge Graph',
            defaults={'description': 'Main knowledge graph for user'}
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Created new knowledge graph for {user.username}')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Using existing knowledge graph for {user.username}')
            )
        
        if async_mode:
            # Queue as background task
            result = rebuild_graph_for_user.delay(user_id)
            self.stdout.write(
                self.style.SUCCESS(f'Graph initialization queued (Task ID: {result.id})')
            )
        else:
            # Run synchronously
            self.stdout.write('Starting graph initialization...')
            result = rebuild_graph_for_user(user_id)
            
            if result.get('success'):
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Graph initialized successfully! {result['items_queued']} items queued for indexing"
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f"Error: {result.get('error', 'Unknown error')}")
                )
