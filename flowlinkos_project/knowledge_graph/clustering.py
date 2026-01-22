"""
Automatic clustering engine for organizing items into smart collections.
Supports K-Means, HDBSCAN, and hierarchical clustering with confidence scoring.
"""

import logging
from typing import List, Dict, Tuple, Optional
import numpy as np
from django.contrib.auth.models import User
from api.models import Item
from knowledge_graph.models import SmartCollection, ClusterItem, Entity
from knowledge_graph.embeddings import get_embedding_service
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

logger = logging.getLogger(__name__)


class AutoClusteringEngine:
    """Engine for automatically clustering items into smart collections."""
    
    def __init__(self, algorithm: str = 'kmeans', min_items: int = 3):
        """
        Initialize clustering engine.
        
        Args:
            algorithm: 'kmeans', 'hdbscan', or 'hierarchical'
            min_items: Minimum items required to form a cluster
        """
        self.algorithm = algorithm
        self.min_items = min_items
        self.embedding_service = get_embedding_service()
    
    def cluster_user_items(self, user: User, force_rebuild: bool = False) -> Dict:
        """
        Cluster all items for a user into smart collections.
        
        Args:
            user: User whose items to cluster
            force_rebuild: If True, delete and recreate all collections
            
        Returns:
            Dict with clustering results: {
                'success': bool,
                'num_clusters': int,
                'avg_confidence': float,
                'collections': [{'name': str, 'confidence': float, 'items': int}]
            }
        """
        try:
            # Get all items for user
            items = Item.objects.filter(user=user)
            if items.count() < self.min_items:
                logger.info(f"User {user.id} has <{self.min_items} items; skipping clustering")
                return {'success': True, 'num_clusters': 0, 'collections': []}
            
            # Extract embeddings from items or entities
            embeddings, item_ids = self._get_item_embeddings(user, items)
            if len(embeddings) < self.min_items:
                logger.warning(f"User {user.id} has insufficient embeddings for clustering")
                return {'success': True, 'num_clusters': 0, 'collections': []}
            
            # Perform clustering
            cluster_labels, optimal_k, silhouette = self._perform_clustering(embeddings)
            
            # Clear old collections if force_rebuild
            if force_rebuild:
                SmartCollection.objects.filter(user=user, is_custom=False).delete()
            
            # Create collections from clusters
            collections = self._create_collections_from_clusters(
                user, items, cluster_labels, item_ids, optimal_k, silhouette
            )
            
            return {
                'success': True,
                'num_clusters': optimal_k,
                'avg_confidence': np.mean([c['confidence'] for c in collections]) if collections else 0.0,
                'collections': collections
            }
        
        except Exception as e:
            logger.error(f"Error clustering items for user {user.id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def _get_item_embeddings(self, user: User, items) -> Tuple[np.ndarray, List[int]]:
        """
        Extract embeddings for items from their content or linked entities.
        
        Returns:
            Tuple of (embeddings array, item_ids list)
        """
        embeddings = []
        item_ids = []
        
        for item in items:
            embedding = None
            
            # Try to get embedding from linked entities
            entity_links = item.entity_links.all()
            if entity_links.exists():
                entity_embeddings = []
                for link in entity_links:
                    if link.entity.embedding:
                        entity_embeddings.append(np.array(link.entity.embedding))
                
                if entity_embeddings:
                    # Average entity embeddings
                    embedding = np.mean(entity_embeddings, axis=0)
            
            # Fallback: generate embedding from item content
            if embedding is None:
                text = f"{item.title} {item.content or ''}"[:1000]
                embed = self.embedding_service.embed_text(text)
                if embed:
                    embedding = np.array(embed)
            
            if embedding is not None:
                embeddings.append(embedding)
                item_ids.append(item.id)
        
        return np.array(embeddings) if embeddings else np.array([]), item_ids
    
    def _perform_clustering(
        self, embeddings: np.ndarray
    ) -> Tuple[np.ndarray, int, float]:
        """
        Perform clustering using the configured algorithm.
        
        Returns:
            Tuple of (cluster_labels, optimal_k, silhouette_score)
        """
        if len(embeddings) == 0:
            return np.array([]), 0, 0.0
        
        # Normalize embeddings
        scaler = StandardScaler()
        embeddings_scaled = scaler.fit_transform(embeddings)
        
        if self.algorithm == 'kmeans':
            return self._kmeans_clustering(embeddings_scaled)
        elif self.algorithm == 'hierarchical':
            return self._hierarchical_clustering(embeddings_scaled)
        else:
            # Default to kmeans
            return self._kmeans_clustering(embeddings_scaled)
    
    def _kmeans_clustering(self, embeddings: np.ndarray) -> Tuple[np.ndarray, int, float]:
        """K-Means clustering with automatic K selection."""
        n_samples = len(embeddings)
        
        # Determine optimal K using elbow method
        if n_samples < 4:
            optimal_k = max(2, n_samples // 2)
        elif n_samples < 20:
            optimal_k = max(2, n_samples // 3)
        else:
            # Use silhouette score to find optimal K
            max_k = min(int(np.sqrt(n_samples)), 20)
            silhouette_scores = []
            
            for k in range(2, max_k + 1):
                kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
                labels = kmeans.fit_predict(embeddings)
                score = silhouette_score(embeddings, labels)
                silhouette_scores.append((k, score))
            
            optimal_k = max(silhouette_scores, key=lambda x: x[1])[0]
        
        # Perform final clustering with optimal K
        kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(embeddings)
        sil_score = silhouette_score(embeddings, labels)
        
        # Normalize silhouette to 0-1 range
        confidence = max(0.0, min(1.0, (sil_score + 1) / 2))
        
        return labels, optimal_k, confidence
    
    def _hierarchical_clustering(self, embeddings: np.ndarray) -> Tuple[np.ndarray, int, float]:
        """Hierarchical agglomerative clustering."""
        n_samples = len(embeddings)
        
        # Determine number of clusters
        if n_samples < 20:
            optimal_k = max(2, n_samples // 3)
        else:
            optimal_k = max(2, int(np.sqrt(n_samples)))
        
        # Perform clustering
        clusterer = AgglomerativeClustering(n_clusters=optimal_k, linkage='ward')
        labels = clusterer.fit_predict(embeddings)
        sil_score = silhouette_score(embeddings, labels)
        
        confidence = max(0.0, min(1.0, (sil_score + 1) / 2))
        
        return labels, optimal_k, confidence
    
    def _create_collections_from_clusters(
        self,
        user: User,
        items,
        cluster_labels: np.ndarray,
        item_ids: List[int],
        optimal_k: int,
        silhouette: float
    ) -> List[Dict]:
        """Create SmartCollection records from cluster labels."""
        collections = []
        item_dict = {item.id: item for item in items}
        
        for cluster_id in range(optimal_k):
            cluster_indices = np.where(cluster_labels == cluster_id)[0]
            cluster_items = [Item.objects.get(id=item_ids[i]) for i in cluster_indices]
            
            if len(cluster_items) < self.min_items:
                continue
            
            # Generate collection name from items
            collection_name = self._generate_collection_name(user, cluster_items)
            
            # Calculate confidence (silhouette score normalized)
            confidence = max(0.3, min(1.0, silhouette * 1.2))
            
            # Infer category
            category = self._infer_category(cluster_items)
            
            # Create or update collection
            collection, created = SmartCollection.objects.update_or_create(
                user=user,
                cluster_id=cluster_id,
                algorithm=self.algorithm,
                defaults={
                    'name': collection_name,
                    'category': category,
                    'confidence_score': confidence,
                    'item_count': len(cluster_items),
                    'is_custom': False,
                }
            )
            
            # Link items to collection
            for item in cluster_items:
                relationship_strength = self._calculate_item_strength(item, cluster_items)
                ClusterItem.objects.update_or_create(
                    collection=collection,
                    item=item,
                    defaults={'relationship_strength': relationship_strength}
                )
            
            # Remove items not in cluster
            ClusterItem.objects.filter(collection=collection).exclude(
                item_id__in=[i.id for i in cluster_items]
            ).delete()
            
            collections.append({
                'id': collection.id,
                'name': collection.name,
                'category': category,
                'confidence': confidence,
                'items': len(cluster_items)
            })
        
        return collections
    
    def _generate_collection_name(self, user: User, items: List[Item]) -> str:
        """Generate a name for the collection based on item titles."""
        if not items:
            return "Untitled Collection"
        
        # Get common words from titles (excluding stopwords)
        stopwords = {'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'by', 'for'}
        all_words = []
        
        for item in items[:5]:  # Use first 5 items
            words = item.title.lower().split()
            all_words.extend([w.strip('.,!?') for w in words if w.strip('.,!?') not in stopwords])
        
        # Find most common words
        from collections import Counter
        common = Counter(all_words).most_common(2)
        
        if common:
            name = ' '.join([word.title() for word, _ in common])
            return name if name else f"Collection {items[0].id}"
        
        return f"{items[0].title[:30]}..."
    
    def _infer_category(self, items: List[Item]) -> str:
        """Infer the category of the collection."""
        # Check for entities of specific types
        entity_types = []
        for item in items:
            entities = item.entity_links.values_list('entity__entity_type', flat=True)
            entity_types.extend(entities)
        
        from collections import Counter
        if entity_types:
            most_common = Counter(entity_types).most_common(1)[0][0]
            if most_common == 'project':
                return 'project'
            elif most_common == 'topic':
                return 'topic'
        
        # Default inference based on content
        return 'theme'
    
    def _calculate_item_strength(self, item: Item, cluster_items: List[Item]) -> float:
        """Calculate relationship strength of item within cluster (0-1)."""
        if len(cluster_items) < 2:
            return 1.0
        
        # Simple heuristic: items with similar titles have higher strength
        item_title_words = set(item.title.lower().split())
        similarities = []
        
        for other in cluster_items:
            if other.id == item.id:
                continue
            other_words = set(other.title.lower().split())
            jaccard = len(item_title_words & other_words) / len(item_title_words | other_words)
            similarities.append(jaccard)
        
        return min(1.0, max(0.5, np.mean(similarities))) if similarities else 0.8


def cluster_items_for_user(user: User, algorithm: str = 'kmeans', force_rebuild: bool = False) -> Dict:
    """Convenience function to cluster items for a user."""
    engine = AutoClusteringEngine(algorithm=algorithm)
    return engine.cluster_user_items(user, force_rebuild=force_rebuild)
