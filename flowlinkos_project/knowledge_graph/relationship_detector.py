"""
Relationship detection engine for identifying connections between entities.
Uses NLP, entity extraction, topic clustering, and semantic similarity.
"""

import logging
from typing import Dict, List, Set, Tuple, Optional
from collections import Counter
import re

import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.tag import pos_tag
from nltk.chunk import ne_chunk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import numpy as np

from knowledge_graph.embeddings import get_embedding_service, EmbeddingService
from knowledge_graph.models import Entity, Relationship, EntityItemLink

logger = logging.getLogger(__name__)

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

try:
    nltk.data.find('taggers/averaged_perceptron_tagger')
except LookupError:
    nltk.download('averaged_perceptron_tagger')

try:
    nltk.data.find('chunkers/maxent_ne_chunker')
except LookupError:
    nltk.download('maxent_ne_chunker')


class EntityExtractor:
    """Extract entities from text using NLP techniques."""
    
    ENTITY_TYPE_MAPPING = {
        'PERSON': 'person',
        'ORGANIZATION': 'organization',
        'GPE': 'place',
        'LOCATION': 'place',
    }
    
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))
        self.min_noun_phrase_length = 2  # minimum words in a noun phrase
    
    def extract_named_entities(self, text: str) -> List[Tuple[str, str]]:
        """
        Extract named entities from text.
        
        Returns:
            List of (entity_text, entity_type) tuples
        """
        try:
            sentences = sent_tokenize(text)
            entities = []
            
            for sentence in sentences:
                tokens = word_tokenize(sentence)
                pos_tags = pos_tag(tokens)
                chunks = ne_chunk(pos_tags)
                
                for chunk in chunks:
                    if hasattr(chunk, 'label'):
                        entity_text = ' '.join(word for word, pos in chunk.leaves())
                        entity_type = self.ENTITY_TYPE_MAPPING.get(chunk.label(), 'other')
                        entities.append((entity_text.lower(), entity_type))
            
            return entities
        except Exception as e:
            logger.error(f"Error extracting named entities: {e}")
            return []
    
    def extract_noun_phrases(self, text: str) -> List[str]:
        """
        Extract noun phrases and important terms.
        
        Returns:
            List of noun phrase strings
        """
        try:
            sentences = sent_tokenize(text)
            noun_phrases = []
            
            for sentence in sentences:
                tokens = word_tokenize(sentence)
                pos_tags = pos_tag(tokens)
                
                # Extract consecutive nouns/adjectives
                current_phrase = []
                for word, pos in pos_tags:
                    if pos.startswith('NN') or pos.startswith('JJ'):
                        if word.lower() not in self.stop_words:
                            current_phrase.append(word)
                    else:
                        if current_phrase and len(current_phrase) >= self.min_noun_phrase_length:
                            noun_phrases.append(' '.join(current_phrase).lower())
                        current_phrase = []
                
                if current_phrase and len(current_phrase) >= self.min_noun_phrase_length:
                    noun_phrases.append(' '.join(current_phrase).lower())
            
            return noun_phrases
        except Exception as e:
            logger.error(f"Error extracting noun phrases: {e}")
            return []
    
    def extract_keywords(self, text: str, top_k: int = 10) -> List[str]:
        """
        Extract important keywords from text.
        
        Returns:
            List of keywords
        """
        try:
            # Remove stopwords and short words
            words = word_tokenize(text.lower())
            keywords = [
                w for w in words
                if w.isalnum() and len(w) > 3 and w not in self.stop_words
            ]
            
            # Get most common
            counter = Counter(keywords)
            return [word for word, _ in counter.most_common(top_k)]
        except Exception as e:
            logger.error(f"Error extracting keywords: {e}")
            return []


class TopicClusterer:
    """Cluster documents into topics for relationship inference."""
    
    def __init__(self, n_topics: int = 5):
        self.n_topics = n_topics
        self.vectorizer = TfidfVectorizer(
            max_features=100,
            stop_words='english',
            ngram_range=(1, 2)
        )
    
    def cluster_texts(self, texts: List[str]) -> Dict[int, List[int]]:
        """
        Cluster texts into topics.
        
        Args:
            texts: List of text documents
            
        Returns:
            Dictionary mapping topic_id to list of document indices
        """
        try:
            if len(texts) < 2:
                return {0: list(range(len(texts)))}
            
            # TF-IDF vectorization
            tfidf_matrix = self.vectorizer.fit_transform(texts)
            
            # Determine optimal number of clusters
            n_clusters = min(self.n_topics, len(texts))
            
            # K-means clustering
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            labels = kmeans.fit_predict(tfidf_matrix)
            
            # Group by topic
            clusters = {}
            for idx, label in enumerate(labels):
                if label not in clusters:
                    clusters[label] = []
                clusters[label].append(idx)
            
            return clusters
        except Exception as e:
            logger.error(f"Error clustering texts: {e}")
            return {0: list(range(len(texts)))}


class RelationshipDetector:
    """Main class for detecting relationships between entities."""
    
    # Common relationship patterns
    RELATIONSHIP_PATTERNS = {
        'mentions': r'\b({entity1}).*?(?:mentions?|discusses?|talks?.*?).*?({entity2})\b',
        'related_to': r'\b({entity1}).*?(?:related to|connected to|associated with).*?({entity2})\b',
        'depends_on': r'\b({entity1}).*?(?:depends on|requires?|needs?).*?({entity2})\b',
        'part_of': r'\b({entity1}).*?(?:part of|component of|part|subset).*?({entity2})\b',
        'similar_to': r'\b({entity1}).*?(?:similar to|like|same as).*?({entity2})\b',
        'created_by': r'\b({entity1}).*?(?:created by|made by|authored by).*?({entity2})\b',
    }
    
    def __init__(self, user_embedding_service: Optional[EmbeddingService] = None):
        self.entity_extractor = EntityExtractor()
        self.topic_clusterer = TopicClusterer()
        self.embedding_service = user_embedding_service or get_embedding_service()
    
    def detect_from_text(
        self,
        text: str,
        user_id: int,
        context: str = ''
    ) -> Dict[str, any]:
        """
        Detect entities and relationships from text.
        
        Args:
            text: Input text to analyze
            user_id: User ID for entity creation
            context: Optional context about the text
            
        Returns:
            Dictionary with detected entities and relationships
        """
        try:
            results = {
                'entities': [],
                'relationships': [],
                'topics': [],
                'keywords': []
            }
            
            # Extract entities
            named_entities = self.entity_extractor.extract_named_entities(text)
            noun_phrases = self.entity_extractor.extract_noun_phrases(text)
            keywords = self.entity_extractor.extract_keywords(text)
            
            results['keywords'] = keywords
            
            # Combine and deduplicate entities
            all_entities = list(set(named_entities + [(np, 'concept') for np in noun_phrases]))
            
            for entity_text, entity_type in all_entities:
                if entity_text and len(entity_text) > 0:
                    embedding = self.embedding_service.embed_text(entity_text)
                    results['entities'].append({
                        'name': entity_text,
                        'type': entity_type,
                        'embedding': embedding,
                        'context': context
                    })
            
            # Detect relationships between entities
            detected_relationships = self._detect_relationships_in_text(text, all_entities)
            results['relationships'] = detected_relationships
            
            return results
        except Exception as e:
            logger.error(f"Error detecting from text: {e}")
            return {
                'entities': [],
                'relationships': [],
                'topics': [],
                'keywords': []
            }
    
    def _detect_relationships_in_text(
        self,
        text: str,
        entities: List[Tuple[str, str]]
    ) -> List[Dict]:
        """Detect relationships between entities in text."""
        relationships = []
        
        if len(entities) < 2:
            return relationships
        
        entity_texts = [e[0] for e in entities]
        
        # Try pattern matching
        for i, (entity1_text, type1) in enumerate(entities):
            for j, (entity2_text, type2) in enumerate(entities):
                if i >= j:
                    continue
                
                for rel_type, pattern in self.RELATIONSHIP_PATTERNS.items():
                    try:
                        regex_pattern = pattern.format(
                            entity1=re.escape(entity1_text),
                            entity2=re.escape(entity2_text)
                        )
                        if re.search(regex_pattern, text, re.IGNORECASE):
                            relationships.append({
                                'source': entity1_text,
                                'target': entity2_text,
                                'type': rel_type,
                                'strength': 0.7
                            })
                            break  # One relationship type per entity pair
                    except Exception as e:
                        logger.debug(f"Pattern matching error: {e}")
                        continue
        
        return relationships
    
    def infer_semantic_relationships(
        self,
        entities_data: List[Dict]
    ) -> List[Dict]:
        """
        Infer relationships based on semantic similarity.
        
        Args:
            entities_data: List of entity dicts with embeddings
            
        Returns:
            List of inferred relationships
        """
        relationships = []
        
        try:
            embeddings = [e.get('embedding') for e in entities_data]
            embeddings = [e for e in embeddings if e is not None]
            
            if len(embeddings) < 2:
                return relationships
            
            # Compute similarity matrix
            similarity_matrix = self.embedding_service.batch_similarity(embeddings, embeddings)
            
            # Find high-similarity pairs
            threshold = 0.6
            for i in range(len(embeddings)):
                for j in range(i + 1, len(embeddings)):
                    sim_score = similarity_matrix[i, j]
                    if sim_score >= threshold:
                        relationships.append({
                            'source': entities_data[i]['name'],
                            'target': entities_data[j]['name'],
                            'type': 'similar_to',
                            'strength': float(sim_score)
                        })
        except Exception as e:
            logger.error(f"Error inferring semantic relationships: {e}")
        
        return relationships
    
    def update_entity_frequencies(
        self,
        entities: List[Dict],
        user_id: int
    ) -> None:
        """Update frequency scores for entities."""
        try:
            from django.contrib.auth.models import User
            user = User.objects.get(id=user_id)
            
            for entity_data in entities:
                entity_obj, _ = Entity.objects.get_or_create(
                    user=user,
                    name=entity_data['name'],
                    entity_type=entity_data.get('type', 'other'),
                    defaults={
                        'embedding': entity_data.get('embedding'),
                        'metadata': {'context': entity_data.get('context', '')}
                    }
                )
                entity_obj.frequency_score += 1
                entity_obj.updated_at = None  # Will use auto_now
                entity_obj.save()
        except Exception as e:
            logger.error(f"Error updating entity frequencies: {e}")


def detect_relationships_from_item(item, embedding_service=None) -> Dict:
    """
    Convenience function to detect relationships from an Item.
    
    Args:
        item: An Item object
        embedding_service: Optional EmbeddingService instance
        
    Returns:
        Dictionary with detected entities and relationships
    """
    detector = RelationshipDetector(embedding_service)
    
    # Combine title and content for analysis
    text = f"{item.title}\n{item.content}"
    context = f"{item.get_item_type_display()} from {item.source.name if item.source else 'unknown source'}"
    
    return detector.detect_from_text(text, item.user_id, context)
