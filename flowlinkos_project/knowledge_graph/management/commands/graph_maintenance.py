"""
Django management command for graph maintenance and cleanup.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from knowledge_graph.models import Entity, Relationship, EntityItemLink, Graph
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Perform maintenance and cleanup on knowledge graphs'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='User ID for specific user (optional)'
        )
        parser.add_argument(
            '--cleanup-threshold',
            type=int,
            default=90,
            help='Delete entities not updated in N days'
        )
        parser.add_argument(
            '--remove-orphans',
            action='store_true',
            help='Remove entities with no relationships'
        )
        parser.add_argument(
            '--update-stats',
            action='store_true',
            help='Update graph statistics'
        )
        parser.add_argument(
            '--remove-duplicates',
            action='store_true',
            help='Consolidate duplicate entities'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without deleting'
        )
    
    def handle(self, *args, **options):
        user_id = options.get('user_id')
        threshold_days = options.get('cleanup_threshold', 90)
        remove_orphans = options.get('remove_orphans', False)
        update_stats = options.get('update_stats', False)
        remove_duplicates = options.get('remove_duplicates', False)
        dry_run = options.get('dry_run', False)
        
        # Determine scope
        if user_id:
            try:
                users = [User.objects.get(id=user_id)]
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'User with ID {user_id} not found'))
                return
        else:
            users = User.objects.all()
        
        for user in users:
            self.stdout.write(f'\nProcessing user: {user.username}')
            
            # Cleanup old entities
            cutoff_date = timezone.now() - timedelta(days=threshold_days)
            old_entities = Entity.objects.filter(
                user=user,
                updated_at__lt=cutoff_date
            )
            old_count = old_entities.count()
            
            if old_count > 0:
                if dry_run:
                    self.stdout.write(f'  Would delete {old_count} old entities')
                else:
                    old_entities.delete()
                    self.stdout.write(self.style.SUCCESS(f'  Deleted {old_count} old entities'))
            
            # Remove orphan entities (no relationships)
            if remove_orphans:
                orphans = Entity.objects.filter(user=user).filter(
                    outgoing_relationships__isnull=True,
                    incoming_relationships__isnull=True
                ).distinct()
                orphan_count = orphans.count()
                
                if orphan_count > 0:
                    if dry_run:
                        self.stdout.write(f'  Would delete {orphan_count} orphan entities')
                    else:
                        orphans.delete()
                        self.stdout.write(self.style.SUCCESS(f'  Deleted {orphan_count} orphan entities'))
            
            # Update stats
            if update_stats:
                graph = Graph.objects.filter(user=user).first()
                if graph:
                    entity_count = Entity.objects.filter(user=user).count()
                    rel_count = Relationship.objects.filter(user=user).count()
                    
                    avg_connections = rel_count / entity_count if entity_count > 0 else 0
                    health_score = min(1.0, avg_connections / 5.0)
                    
                    graph.entity_count = entity_count
                    graph.relationship_count = rel_count
                    graph.health_score = health_score
                    graph.save()
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  Updated stats: {entity_count} entities, {rel_count} relationships, health: {health_score:.2f}'
                        )
                    )
            
            # Remove duplicate entities
            if remove_duplicates:
                self._remove_duplicate_entities(user, dry_run)
        
        self.stdout.write(self.style.SUCCESS('\nMaintenance completed!'))
    
    def _remove_duplicate_entities(self, user: User, dry_run: bool = False):
        """Remove duplicate entities (same name, different case)."""
        from django.db.models import Count
        
        # Find entities with same name (case-insensitive)
        duplicates = Entity.objects.filter(user=user).values('name_lower').annotate(
            count=Count('id')
        ).filter(count__gt=1)
        
        total_removed = 0
        
        for dup in duplicates:
            entities = Entity.objects.filter(
                user=user,
                name__iexact=dup['name_lower']
            ).order_by('frequency_score')
            
            # Keep the one with highest frequency, merge others
            primary = entities.first()
            duplicates_to_merge = entities[1:]
            
            for dup_entity in duplicates_to_merge:
                # Merge relationships
                for rel in dup_entity.outgoing_relationships.all():
                    Relationship.objects.get_or_create(
                        user=user,
                        source_entity=primary,
                        target_entity=rel.target_entity,
                        relationship_type=rel.relationship_type,
                        defaults={'strength': max(rel.strength, 0.5)}
                    )
                
                for rel in dup_entity.incoming_relationships.all():
                    Relationship.objects.get_or_create(
                        user=user,
                        source_entity=rel.source_entity,
                        target_entity=primary,
                        relationship_type=rel.relationship_type,
                        defaults={'strength': max(rel.strength, 0.5)}
                    )
                
                # Update frequency
                primary.frequency_score += dup_entity.frequency_score
                
                if not dry_run:
                    dup_entity.delete()
                    total_removed += 1
        
        if total_removed > 0:
            if dry_run:
                self.stdout.write(f'  Would remove {total_removed} duplicate entities')
            else:
                self.stdout.write(self.style.SUCCESS(f'  Removed {total_removed} duplicate entities'))
