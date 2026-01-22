"""
Data ingestion pipeline for extracting and normalizing data from various sources.
Handles notes, files, messages, bookmarks, and tasks.
"""

import logging
import os
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from abc import ABC, abstractmethod

from api.models import Item
from core.models import Source
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


class DataExtractor(ABC):
    """Abstract base class for extracting data from different sources."""
    
    def __init__(self, source: Source, user: User):
        self.source = source
        self.user = user
    
    @abstractmethod
    def extract(self) -> List[Dict]:
        """Extract data from source and return list of normalized items."""
        pass
    
    def normalize_item(
        self,
        item_type: str,
        title: str,
        content: str,
        metadata: Optional[Dict] = None,
        tags: Optional[List[str]] = None,
        priority: int = 0
    ) -> Dict:
        """Normalize extracted data into standard format."""
        return {
            'item_type': item_type,
            'title': title[:500],  # Limit title
            'content': content,
            'metadata': metadata or {},
            'tags': ','.join(tags) if tags else '',
            'priority': priority,
            'source_id': self.source.id,
            'user_id': self.user.id
        }


class NoteExtractor(DataExtractor):
    """Extractor for note items."""
    
    def extract(self) -> List[Dict]:
        """Extract note items from the database."""
        items = Item.objects.filter(
            user=self.user,
            source=self.source,
            item_type='note',
            is_archived=False
        )
        
        extracted = []
        for item in items:
            normalized = self.normalize_item(
                item_type='note',
                title=item.title,
                content=item.content,
                metadata=item.metadata,
                tags=item.tags.split(',') if item.tags else [],
                priority=item.priority
            )
            extracted.append(normalized)
        
        logger.info(f"Extracted {len(extracted)} notes")
        return extracted


class FileExtractor(DataExtractor):
    """Extractor for file items."""
    
    def extract(self) -> List[Dict]:
        """Extract file items from the database."""
        items = Item.objects.filter(
            user=self.user,
            source=self.source,
            item_type='file',
            is_archived=False
        )
        
        extracted = []
        for item in items:
            # Extract file metadata
            metadata = item.metadata.copy() if item.metadata else {}
            metadata['file_name'] = metadata.get('file_name', item.title)
            metadata['file_size'] = metadata.get('file_size', 0)
            metadata['file_type'] = metadata.get('file_type', 'unknown')
            
            normalized = self.normalize_item(
                item_type='file',
                title=item.title,
                content=item.content,
                metadata=metadata,
                tags=item.tags.split(',') if item.tags else [],
                priority=item.priority
            )
            extracted.append(normalized)
        
        logger.info(f"Extracted {len(extracted)} files")
        return extracted


class MessageExtractor(DataExtractor):
    """Extractor for message items."""
    
    def extract(self) -> List[Dict]:
        """Extract message items from the database."""
        items = Item.objects.filter(
            user=self.user,
            source=self.source,
            item_type='message',
            is_archived=False
        )
        
        extracted = []
        for item in items:
            metadata = item.metadata.copy() if item.metadata else {}
            metadata['sender'] = metadata.get('sender', 'Unknown')
            metadata['channel'] = metadata.get('channel', 'Direct')
            
            normalized = self.normalize_item(
                item_type='message',
                title=f"Message from {metadata['sender']}",
                content=item.content,
                metadata=metadata,
                tags=item.tags.split(',') if item.tags else [],
                priority=item.priority
            )
            extracted.append(normalized)
        
        logger.info(f"Extracted {len(extracted)} messages")
        return extracted


class BookmarkExtractor(DataExtractor):
    """Extractor for bookmark items."""
    
    def extract(self) -> List[Dict]:
        """Extract bookmark items from the database."""
        items = Item.objects.filter(
            user=self.user,
            source=self.source,
            item_type='bookmark',
            is_archived=False
        )
        
        extracted = []
        for item in items:
            metadata = item.metadata.copy() if item.metadata else {}
            metadata['url'] = metadata.get('url', '')
            metadata['domain'] = metadata.get('domain', 'unknown')
            
            normalized = self.normalize_item(
                item_type='bookmark',
                title=item.title,
                content=item.content,
                metadata=metadata,
                tags=item.tags.split(',') if item.tags else [],
                priority=item.priority
            )
            extracted.append(normalized)
        
        logger.info(f"Extracted {len(extracted)} bookmarks")
        return extracted


class TaskExtractor(DataExtractor):
    """Extractor for task items."""
    
    def extract(self) -> List[Dict]:
        """Extract task items from the database."""
        items = Item.objects.filter(
            user=self.user,
            source=self.source,
            item_type='task',
            is_archived=False
        )
        
        extracted = []
        for item in items:
            metadata = item.metadata.copy() if item.metadata else {}
            metadata['status'] = metadata.get('status', 'todo')
            metadata['due_date'] = metadata.get('due_date')
            metadata['assignee'] = metadata.get('assignee')
            
            normalized = self.normalize_item(
                item_type='task',
                title=item.title,
                content=item.content,
                metadata=metadata,
                tags=item.tags.split(',') if item.tags else [],
                priority=item.priority
            )
            extracted.append(normalized)
        
        logger.info(f"Extracted {len(extracted)} tasks")
        return extracted


class DataIngestionPipeline:
    """Main pipeline for ingesting data from all sources."""
    
    EXTRACTORS = {
        'notes': NoteExtractor,
        'files': FileExtractor,
        'messages': MessageExtractor,
        'bookmarks': BookmarkExtractor,
        'tasks': TaskExtractor,
    }
    
    def __init__(self, user: User):
        self.user = user
    
    def ingest_all(self) -> Dict:
        """Ingest data from all active sources."""
        results = {
            'total_items': 0,
            'by_type': {},
            'by_source': {},
            'errors': []
        }
        
        sources = Source.objects.filter(user=self.user, is_active=True)
        
        for source in sources:
            try:
                extractor_class = self.EXTRACTORS.get(source.source_type)
                if not extractor_class:
                    logger.warning(f"No extractor for source type: {source.source_type}")
                    continue
                
                extractor = extractor_class(source, self.user)
                items = extractor.extract()
                
                results['total_items'] += len(items)
                results['by_source'][source.name] = len(items)
                
                for item in items:
                    item_type = item['item_type']
                    results['by_type'][item_type] = results['by_type'].get(item_type, 0) + 1
                
            except Exception as e:
                logger.error(f"Error ingesting from {source.name}: {e}")
                results['errors'].append(f"{source.name}: {str(e)}")
        
        logger.info(f"Ingestion pipeline completed: {results}")
        return results
    
    def ingest_source(self, source_type: str) -> Dict:
        """Ingest data from a specific source type."""
        results = {
            'total_items': 0,
            'items': [],
            'errors': []
        }
        
        sources = Source.objects.filter(
            user=self.user,
            source_type=source_type,
            is_active=True
        )
        
        for source in sources:
            try:
                extractor_class = self.EXTRACTORS.get(source_type)
                if not extractor_class:
                    logger.warning(f"No extractor for source type: {source_type}")
                    continue
                
                extractor = extractor_class(source, self.user)
                items = extractor.extract()
                
                results['total_items'] += len(items)
                results['items'].extend(items)
                
            except Exception as e:
                logger.error(f"Error ingesting {source_type}: {e}")
                results['errors'].append(str(e))
        
        return results
    
    def ingest_single_item(self, item: Item) -> Dict:
        """Ingest and normalize a single item."""
        try:
            if not item.source:
                return {'success': False, 'error': 'Item has no source'}
            
            extractor_class = self.EXTRACTORS.get(item.source.source_type)
            if not extractor_class:
                return {'success': False, 'error': f'Unknown source type: {item.source.source_type}'}
            
            extractor = extractor_class(item.source, self.user)
            normalized = extractor.normalize_item(
                item_type=item.item_type,
                title=item.title,
                content=item.content,
                metadata=item.metadata,
                tags=item.tags.split(',') if item.tags else [],
                priority=item.priority
            )
            
            return {
                'success': True,
                'item': normalized
            }
        except Exception as e:
            logger.error(f"Error ingesting single item: {e}")
            return {'success': False, 'error': str(e)}


def get_ingestion_pipeline(user: User) -> DataIngestionPipeline:
    """Factory function to get ingestion pipeline for a user."""
    return DataIngestionPipeline(user)
