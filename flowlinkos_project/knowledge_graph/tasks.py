"""
Celery background tasks for knowledge graph updates and indexing.
Handles asynchronous processing of data ingestion and relationship detection.
"""

import logging
from celery import shared_task
from django.contrib.auth.models import User
from django.db import transaction

from api.models import Item
from knowledge_graph.models import Entity, Relationship, EntityItemLink, Graph
from knowledge_graph.ingestion import get_ingestion_pipeline
from knowledge_graph.relationship_detector import (
    RelationshipDetector,
    detect_relationships_from_item
)
from knowledge_graph.embeddings import get_embedding_service

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def index_item_in_graph(self, item_id: int, user_id: int):
    """
    Index a single item into the knowledge graph.
    
    Args:
        item_id: ID of the Item to index
        user_id: ID of the User
    """
    try:
        item = Item.objects.get(id=item_id, user_id=user_id)
        user = User.objects.get(id=user_id)
        
        # Detect relationships from item
        detector = RelationshipDetector()
        results = detect_relationships_from_item(item)
        
        with transaction.atomic():
            # Create or update entities
            entities_created = []
            for entity_data in results.get('entities', []):
                entity, created = Entity.objects.update_or_create(
                    user=user,
                    name=entity_data['name'],
                    entity_type=entity_data.get('type', 'other'),
                    defaults={
                        'embedding': entity_data.get('embedding'),
                        'metadata': {'context': entity_data.get('context', '')},
                        'frequency_score': 1
                    }
                )
                
                if not created:
                    entity.frequency_score += 1
                    entity.save(update_fields=['frequency_score'])
                
                entities_created.append(entity)
                
                # Link entity to item
                EntityItemLink.objects.get_or_create(
                    entity=entity,
                    item=item,
                    defaults={'mention_count': 1, 'context': entity_data.get('context', '')}
                )
            
            # Create relationships between entities
            for rel_data in results.get('relationships', []):
                source_entity = Entity.objects.filter(
                    user=user,
                    name=rel_data['source']
                ).first()
                target_entity = Entity.objects.filter(
                    user=user,
                    name=rel_data['target']
                ).first()
                
                if source_entity and target_entity:
                    Relationship.objects.update_or_create(
                        user=user,
                        source_entity=source_entity,
                        target_entity=target_entity,
                        relationship_type=rel_data.get('type', 'related_to'),
                        defaults={
                            'strength': rel_data.get('strength', 0.5),
                            'metadata': {'detected_from_item': item_id}
                        }
                    )
        
        logger.info(f"Successfully indexed item {item_id} for user {user_id}")
        return {
            'success': True,
            'item_id': item_id,
            'entities_found': len(results.get('entities', [])),
            'relationships_found': len(results.get('relationships', []))
        }
    
    except Item.DoesNotExist:
        logger.error(f"Item {item_id} not found")
        return {'success': False, 'error': 'Item not found'}
    
    except Exception as exc:
        logger.error(f"Error indexing item {item_id}: {exc}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task(bind=True, max_retries=3)
def batch_index_items(self, user_id: int, item_ids: list = None):
    """
    Batch index multiple items into the knowledge graph.
    
    Args:
        user_id: ID of the User
        item_ids: List of Item IDs to index (None = all unindexed items)
    """
    try:
        user = User.objects.get(id=user_id)
        
        if item_ids:
            items = Item.objects.filter(id__in=item_ids, user=user, is_archived=False)
        else:
            # Index items that don't have entities yet
            indexed_item_ids = EntityItemLink.objects.filter(
                entity__user=user
            ).values_list('item_id', flat=True).distinct()
            items = Item.objects.filter(user=user, is_archived=False).exclude(
                id__in=indexed_item_ids
            )
        
        total_items = items.count()
        logger.info(f"Starting batch indexing of {total_items} items for user {user_id}")
        
        results = {
            'total': total_items,
            'successful': 0,
            'failed': 0,
            'entities_created': 0,
            'relationships_created': 0
        }
        
        for item in items:
            try:
                task_result = index_item_in_graph(item.id, user_id)
                if task_result.get('success'):
                    results['successful'] += 1
                    results['entities_created'] += task_result.get('entities_found', 0)
                    results['relationships_created'] += task_result.get('relationships_found', 0)
                else:
                    results['failed'] += 1
            except Exception as item_exc:
                logger.error(f"Error in batch indexing item {item.id}: {item_exc}")
                results['failed'] += 1
        
        logger.info(f"Batch indexing completed: {results}")
        
        # Trigger auto-clustering after batch indexing
        if results['successful'] > 0:
            auto_cluster_new_items.delay(user_id, list(items.values_list('id', flat=True)))
        
        return results
    
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
        return {'success': False, 'error': 'User not found'}
    
    except Exception as exc:
        logger.error(f"Error in batch indexing: {exc}")
        raise self.retry(exc=exc, countdown=300 * (2 ** self.request.retries))


@shared_task(bind=True, max_retries=2)
def update_graph_snapshot(self, user_id: int, graph_id: int = None):
    """
    Update graph snapshot with current statistics.
    
    Args:
        user_id: ID of the User
        graph_id: ID of specific Graph (None = create/update default)
    """
    try:
        user = User.objects.get(id=user_id)
        
        # Get or create default graph
        if graph_id:
            graph = Graph.objects.get(id=graph_id, user=user)
        else:
            graph, _ = Graph.objects.get_or_create(
                user=user,
                name='Main Knowledge Graph',
                defaults={'description': 'Main knowledge graph for user'}
            )
        
        # Update statistics
        entity_count = Entity.objects.filter(user=user).count()
        relationship_count = Relationship.objects.filter(user=user).count()
        
        # Calculate health score (based on entity/relationship ratio)
        if entity_count > 0:
            avg_relationships_per_entity = relationship_count / entity_count
            health_score = min(1.0, avg_relationships_per_entity / 5.0)  # Normalize to 0-1
        else:
            health_score = 0.0
        
        graph.entity_count = entity_count
        graph.relationship_count = relationship_count
        graph.health_score = health_score
        graph.save()
        
        logger.info(f"Updated graph snapshot: {entity_count} entities, {relationship_count} relationships")
        return {
            'success': True,
            'entity_count': entity_count,
            'relationship_count': relationship_count,
            'health_score': health_score
        }
    
    except (User.DoesNotExist, Graph.DoesNotExist) as e:
        logger.error(f"Error updating graph snapshot: {e}")
        return {'success': False, 'error': str(e)}
    
    except Exception as exc:
        logger.error(f"Unexpected error updating graph: {exc}")
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task(bind=True, max_retries=3)
def ingest_from_source(self, user_id: int, source_type: str = None):
    """
    Ingest data from configured sources.
    
    Args:
        user_id: ID of the User
        source_type: Optional specific source type to ingest
    """
    try:
        user = User.objects.get(id=user_id)
        pipeline = get_ingestion_pipeline(user)
        
        if source_type:
            ingest_result = pipeline.ingest_source(source_type)
            logger.info(f"Ingested {ingest_result['total_items']} items from {source_type}")
        else:
            ingest_result = pipeline.ingest_all()
            logger.info(f"Ingestion complete: {ingest_result}")
        
        # Trigger graph update
        update_graph_snapshot.delay(user_id)
        
        return ingest_result
    
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
        return {'success': False, 'error': 'User not found'}
    
    except Exception as exc:
        logger.error(f"Error in ingestion: {exc}")
        raise self.retry(exc=exc, countdown=120 * (2 ** self.request.retries))


@shared_task
def delete_old_relationships(days: int = 90):
    """
    Clean up old relationships that haven't been updated.
    
    Args:
        days: Delete relationships older than this many days
    """
    try:
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=days)
        old_relationships = Relationship.objects.filter(updated_at__lt=cutoff_date)
        count, _ = old_relationships.delete()
        
        logger.info(f"Deleted {count} old relationships")
        return {'success': True, 'deleted': count}
    
    except Exception as e:
        logger.error(f"Error deleting old relationships: {e}")
        return {'success': False, 'error': str(e)}


@shared_task
def rebuild_graph_for_user(user_id: int):
    """
    Completely rebuild knowledge graph for a user.
    
    Args:
        user_id: ID of the User
    """
    try:
        user = User.objects.get(id=user_id)
        
        # Clear existing graph data
        Entity.objects.filter(user=user).delete()
        Relationship.objects.filter(user=user).delete()
        EntityItemLink.objects.filter(entity__user=user).delete()
        
        logger.info(f"Cleared graph data for user {user_id}")
        
        # Reingest all data
        ingest_result = ingest_from_source(user_id)
        logger.info(f"Reingested all data: {ingest_result}")
        
        # Index all items
        items = Item.objects.filter(user=user, is_archived=False)
        item_ids = list(items.values_list('id', flat=True))
        
        batch_index_items.delay(user_id, item_ids)
        
        return {'success': True, 'items_queued': len(item_ids)}
    
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
        return {'success': False, 'error': 'User not found'}
    
    except Exception as e:
        logger.error(f"Error rebuilding graph: {e}")
        return {'success': False, 'error': str(e)}

@shared_task(bind=True, max_retries=3)
def refresh_auto_clusters(self, user_id: int, algorithm: str = 'kmeans', force_rebuild: bool = False):
    """
    Refresh smart collections (auto-clustering) for a user.
    
    Args:
        user_id: ID of the User
        algorithm: Clustering algorithm ('kmeans', 'hdbscan', 'hierarchical')
        force_rebuild: If True, delete old collections and rebuild
    """
    try:
        user = User.objects.get(id=user_id)
        
        from knowledge_graph.clustering import AutoClusteringEngine
        
        engine = AutoClusteringEngine(algorithm=algorithm)
        result = engine.cluster_user_items(user, force_rebuild=force_rebuild)
        
        logger.info(f"Clustering complete for user {user_id}: {result}")
        return result
    
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
        return {'success': False, 'error': 'User not found'}
    
    except Exception as e:
        logger.error(f"Error in refresh_auto_clusters: {e}")
        if self.request.retries < self.max_retries:
            self.retry(exc=e, countdown=60)
        return {'success': False, 'error': str(e)}


@shared_task(bind=True, max_retries=2)
def merge_collections_task(self, user_id: int, source_id: int, target_id: int, new_name: str):
    """
    Merge two smart collections (background task).
    
    Args:
        user_id: ID of the User
        source_id: ID of source SmartCollection
        target_id: ID of target SmartCollection
        new_name: Name for merged collection
    """
    try:
        user = User.objects.get(id=user_id)
        from knowledge_graph.models import SmartCollection, ClusterItem
        
        source = SmartCollection.objects.get(id=source_id, user=user)
        target = SmartCollection.objects.get(id=target_id, user=user)
        
        with transaction.atomic():
            # Move all items from source to target
            source_items = ClusterItem.objects.filter(collection=source)
            for item in source_items:
                ClusterItem.objects.update_or_create(
                    collection=target,
                    item=item.item,
                    defaults={'relationship_strength': item.relationship_strength}
                )
            
            # Update target
            target.name = new_name
            target.item_count = target.items.count()
            target.is_custom = True
            target.save()
            
            # Delete source
            source.delete()
            
            logger.info(f"Collections {source_id} and {target_id} merged for user {user_id}")
            return {
                'success': True,
                'message': f"Merged into '{new_name}'",
                'collection_id': target.id
            }
    
    except (SmartCollection.DoesNotExist, User.DoesNotExist) as e:
        logger.error(f"Error in merge_collections_task: {e}")
        return {'success': False, 'error': str(e)}
    
    except Exception as e:
        logger.error(f"Error merging collections: {e}")
        if self.request.retries < self.max_retries:
            self.retry(exc=e, countdown=30)
        return {'success': False, 'error': str(e)}


@shared_task
def auto_cluster_new_items(user_id: int, item_ids: list):
    """
    Trigger clustering update when new items are added.
    
    Args:
        user_id: ID of the User
        item_ids: List of newly added Item IDs
    """
    try:
        user = User.objects.get(id=user_id)
        
        # Run clustering with slight delay to batch updates
        from knowledge_graph.clustering import cluster_items_for_user
        result = cluster_items_for_user(user, algorithm='kmeans', force_rebuild=False)
        
        logger.info(f"Auto-clustering triggered for user {user_id} with {len(item_ids)} new items")
        return result
    
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
        return {'success': False, 'error': 'User not found'}
    
    except Exception as e:
        logger.error(f"Error in auto_cluster_new_items: {e}")
        return {'success': False, 'error': str(e)}