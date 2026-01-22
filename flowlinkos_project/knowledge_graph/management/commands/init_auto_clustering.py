"""
Django management command to initialize auto-clustering for users.
Clusters existing items into smart collections.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db.models import Count
from knowledge_graph.clustering import cluster_items_for_user


class Command(BaseCommand):
    help = 'Initialize auto-clustering (smart collections) for users'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='Specific user ID to cluster (default: all users)',
        )
        parser.add_argument(
            '--algorithm',
            type=str,
            default='kmeans',
            choices=['kmeans', 'hdbscan', 'hierarchical'],
            help='Clustering algorithm to use (default: kmeans)',
        )
        parser.add_argument(
            '--force-rebuild',
            action='store_true',
            help='Force rebuild existing collections',
        )
        parser.add_argument(
            '--min-items',
            type=int,
            default=3,
            help='Minimum items required to form cluster (default: 3)',
        )
    
    def handle(self, *args, **options):
        user_id = options.get('user_id')
        algorithm = options.get('algorithm', 'kmeans')
        force_rebuild = options.get('force_rebuild', False)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n🔄 Starting Auto-Clustering Engine\n'
                f'   Algorithm: {algorithm}\n'
                f'   Force Rebuild: {force_rebuild}\n'
            )
        )
        
        # Get users to cluster
        if user_id:
            try:
                users = User.objects.filter(id=user_id)
                if not users.exists():
                    self.stdout.write(
                        self.style.ERROR(f'User {user_id} not found')
                    )
                    return
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'User {user_id} not found')
                )
                return
        else:
            # Get all users with items
            from api.models import Item
            users = User.objects.filter(
                item__user_id=User.id
            ).distinct()
        
        if not users.exists():
            self.stdout.write(
                self.style.WARNING('No users found with items')
            )
            return
        
        total_users = users.count()
        self.stdout.write(
            f'\n📊 Found {total_users} user(s) to cluster\n'
        )
        
        success_count = 0
        failed_count = 0
        total_collections = 0
        total_items_organized = 0
        
        for idx, user in enumerate(users, 1):
            try:
                self.stdout.write(
                    f'[{idx}/{total_users}] Processing user: {user.username} (ID: {user.id})'
                )
                
                # Cluster items
                result = cluster_items_for_user(
                    user,
                    algorithm=algorithm,
                    force_rebuild=force_rebuild
                )
                
                if result.get('success'):
                    num_clusters = result.get('num_clusters', 0)
                    avg_confidence = result.get('avg_confidence', 0.0)
                    
                    # Count items organized
                    from knowledge_graph.models import ClusterItem
                    items_count = ClusterItem.objects.filter(
                        collection__user=user
                    ).count()
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✓ Created {num_clusters} collections '
                            f'(avg confidence: {avg_confidence:.2f}) '
                            f'with {items_count} items'
                        )
                    )
                    
                    success_count += 1
                    total_collections += num_clusters
                    total_items_organized += items_count
                    
                    # Print collections
                    if result.get('collections'):
                        for coll in result['collections'][:5]:
                            self.stdout.write(
                                f'    - {coll["name"]} ({coll["items"]} items, '
                                f'confidence: {coll["confidence"]:.2f})'
                            )
                        if len(result['collections']) > 5:
                            self.stdout.write(
                                f'    ... and {len(result["collections"]) - 5} more'
                            )
                else:
                    error = result.get('error', 'Unknown error')
                    self.stdout.write(
                        self.style.ERROR(f'  ✗ Error: {error}')
                    )
                    failed_count += 1
            
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Exception: {str(e)}')
                )
                failed_count += 1
        
        # Summary
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('✓ AUTO-CLUSTERING COMPLETE'))
        self.stdout.write('=' * 60)
        self.stdout.write(f'Success:            {success_count}/{total_users}')
        self.stdout.write(f'Failed:             {failed_count}/{total_users}')
        self.stdout.write(f'Total Collections:  {total_collections}')
        self.stdout.write(f'Items Organized:    {total_items_organized}')
        self.stdout.write('=' * 60 + '\n')
        
        if success_count == total_users:
            self.stdout.write(
                self.style.SUCCESS('All users clustered successfully!')
            )
        elif success_count > 0:
            self.stdout.write(
                self.style.WARNING(
                    f'Partial success: {success_count} user(s) completed'
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR('No users were successfully clustered')
            )
