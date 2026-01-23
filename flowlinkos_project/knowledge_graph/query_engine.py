"""
Query engine for intent classification, parsing, and routing to graph/items.
Uses lightweight zero-shot intent scoring via embeddings and heuristic routing.
"""

import logging
import re
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple, Any
from datetime import timedelta, datetime
from django.utils import timezone
from django.db.models import Q

from api.models import Item, Summary
from knowledge_graph.models import SmartCollection
from knowledge_graph.embeddings import get_embedding_service

logger = logging.getLogger(__name__)


@dataclass
class IntentDefinition:
    name: str
    description: str
    examples: List[str]


INTENT_DEFINITIONS: List[IntentDefinition] = [
    IntentDefinition(
        name="schedule",
        description="Plans, schedules, deadlines, next steps, time-bound asks",
        examples=[
            "What did I plan for next week?",
            "What deadlines do I have soon?",
            "What are my tasks tomorrow?",
            "Upcoming meetings",
        ],
    ),
    IntentDefinition(
        name="projects",
        description="Projects, themes, smart collections, grouped work",
        examples=[
            "Show my projects",
            "What themes am I working on?",
            "Show my research clusters",
            "Smart collections about design",
        ],
    ),
    IntentDefinition(
        name="summaries",
        description="Summaries, recaps, briefs",
        examples=[
            "Summarize this week",
            "Give me a recap",
            "What happened yesterday?",
        ],
    ),
    IntentDefinition(
        name="people",
        description="People, contacts, collaborators",
        examples=[
            "What did I discuss with Alice?",
            "Follow-ups for Bob",
        ],
    ),
    IntentDefinition(
        name="search",
        description="Generic search when no strong intent",
        examples=[
            "Find notes about budget",
            "Search for onboarding",
            "Look up design tokens",
        ],
    ),
]

INTENT_THRESHOLD = 0.55
FALLBACK_THRESHOLD = 0.35
MAX_RESULTS = 10


class IntentClassifier:
    """Lightweight zero-shot intent classifier using embeddings."""

    def __init__(self):
        self.embedding_service = get_embedding_service()
        self.intent_embeddings: Dict[str, List[List[float]]] = self._precompute_intent_embeddings()

    def _precompute_intent_embeddings(self) -> Dict[str, List[List[float]]]:
        embeddings: Dict[str, List[List[float]]] = {}
        for intent in INTENT_DEFINITIONS:
            vectors: List[List[float]] = []
            for phrase in intent.examples:
                emb = self.embedding_service.embed_text(phrase)
                if emb:
                    vectors.append(emb)
            embeddings[intent.name] = vectors
        return embeddings

    def classify(self, query_text: str) -> Tuple[str, float]:
        query_embedding = self.embedding_service.embed_text(query_text)
        if not query_embedding:
            return "search", 0.0

        best_intent = "search"
        best_score = 0.0

        for intent in INTENT_DEFINITIONS:
            vectors = self.intent_embeddings.get(intent.name, [])
            for vec in vectors:
                score = self.embedding_service.compute_similarity(query_embedding, vec)
                if score > best_score:
                    best_score = score
                    best_intent = intent.name

        return best_intent, float(best_score)


class QueryRouter:
    """Routes natural-language queries to handlers and returns structured answers."""

    def __init__(self):
        self.classifier = IntentClassifier()
        self.embedding_service = get_embedding_service()

    def execute(self, user, query_text: str) -> Dict[str, Any]:
        intent, intent_conf = self.classifier.classify(query_text)
        timeframe = self._parse_timeframe(query_text)

        handler = {
            "schedule": self._handle_schedule,
            "projects": self._handle_projects,
            "summaries": self._handle_summaries,
            "people": self._handle_people,
            "search": self._handle_search,
        }.get(intent, self._handle_search)

        results, answer, result_conf = handler(user, query_text, timeframe)

        confidence = float(min(1.0, max(intent_conf, result_conf)))
        fallback = confidence < INTENT_THRESHOLD

        # If confidence is low, provide a safe fallback search
        if fallback and intent != "search":
            search_results, search_answer, search_conf = self._handle_search(user, query_text, timeframe)
            # Prefer better of the two
            if search_conf >= confidence:
                results = search_results
                answer = search_answer
                confidence = search_conf
                intent = "search"
                fallback = confidence < INTENT_THRESHOLD

        return {
            "intent": intent,
            "intent_confidence": round(intent_conf, 3),
            "confidence": round(confidence, 3),
            "answer": answer,
            "results": results,
            "fallback": fallback,
            "timeframe": timeframe,
        }

    def _parse_timeframe(self, query_text: str) -> Optional[Dict[str, str]]:
        """Parse simple relative time expressions like today/tomorrow/next week/last week/next month."""
        text = query_text.lower()
        now = timezone.now()

        def window(start_dt: datetime, end_dt: datetime, label: str) -> Dict[str, str]:
            return {"label": label, "start": start_dt.isoformat(), "end": end_dt.isoformat()}

        if "next week" in text:
            start = now + timedelta(days=(7 - now.weekday()))
            end = start + timedelta(days=7)
            return window(start, end, "next_week")
        if "last week" in text:
            end = now - timedelta(days=now.weekday())
            start = end - timedelta(days=7)
            return window(start, end, "last_week")
        if "this week" in text or "current week" in text:
            start = now - timedelta(days=now.weekday())
            end = start + timedelta(days=7)
            return window(start, end, "this_week")
        if "next month" in text:
            start = (now + timedelta(days=32)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            # start of following month
            end = (start + timedelta(days=32)).replace(day=1)
            return window(start, end, "next_month")
        if "last month" in text:
            start = (now.replace(day=1) - timedelta(days=1)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            return window(start, end, "last_month")
        if "tomorrow" in text:
            start = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)
            return window(start, end, "tomorrow")
        if "yesterday" in text:
            end = now.replace(hour=0, minute=0, second=0, microsecond=0)
            start = end - timedelta(days=1)
            return window(start, end, "yesterday")
        if "today" in text:
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)
            return window(start, end, "today")

        # Absolute day mention: "on 2026-01-23" or mm/dd
        date_match = re.search(r"(20\d{2}-\d{2}-\d{2})|(\d{1,2}/\d{1,2})", text)
        if date_match:
            try:
                raw = date_match.group(1) or date_match.group(2)
                if "/" in raw:
                    month, day = raw.split("/")
                    year = now.year
                    dt = datetime(year=int(year), month=int(month), day=int(day), tzinfo=now.tzinfo)
                else:
                    dt = datetime.fromisoformat(raw).replace(tzinfo=now.tzinfo)
                start = dt.replace(hour=0, minute=0, second=0, microsecond=0)
                end = start + timedelta(days=1)
                return window(start, end, "date")
            except Exception:
                pass
        return None

    def _handle_schedule(self, user, query_text: str, timeframe: Optional[Dict[str, str]]):
        queryset = Item.objects.filter(user=user, item_type="task")
        if timeframe and timeframe.get("start") and timeframe.get("end"):
            start_dt = self._to_dt(timeframe["start"])
            end_dt = self._to_dt(timeframe["end"])
            if start_dt and end_dt:
                queryset = queryset.filter(
                    created_at__gte=start_dt,
                    created_at__lte=end_dt,
                )

        items = list(queryset.order_by("-priority", "-created_at")[:MAX_RESULTS])
        results = [self._item_to_result(i, score=0.7) for i in items]
        answer = "No scheduled tasks found." if not items else "Here are your upcoming tasks."
        return results, answer, 0.65 if items else 0.35

    def _handle_projects(self, user, query_text: str, timeframe: Optional[Dict[str, str]]):
        collections = SmartCollection.objects.filter(user=user).order_by("-confidence_score")[:MAX_RESULTS]
        results = [self._collection_to_result(c) for c in collections]
        answer = "No smart collections found." if not results else "Here are your top smart collections."
        return results, answer, 0.7 if results else 0.4

    def _handle_summaries(self, user, query_text: str, timeframe: Optional[Dict[str, str]]):
        summaries = Summary.objects.filter(user=user).order_by("-created_at")[:MAX_RESULTS]
        results = [
            {
                "type": "summary",
                "id": s.id,
                "title": s.title,
                "summary_text": s.summary_text[:240],
                "summary_type": s.summary_type,
                "url": f"/api/summaries/{s.id}/",
            }
            for s in summaries
        ]
        answer = "No summaries available yet." if not results else "Recent summaries ready."
        return results, answer, 0.65 if results else 0.35

    def _handle_people(self, user, query_text: str, timeframe: Optional[Dict[str, str]]):
        # Heuristic: search items mentioning capitalized names (simplified) or keywords
        keywords = [word for word in query_text.split() if word.istitle()]
        q_objects = Q()
        for kw in keywords:
            q_objects |= Q(title__icontains=kw) | Q(content__icontains=kw)
        if not q_objects:
            q_objects = Q(title__icontains=query_text) | Q(content__icontains=query_text)

        items = list(Item.objects.filter(user=user).filter(q_objects).order_by("-created_at")[:MAX_RESULTS])
        results = [self._item_to_result(i, score=0.6) for i in items]
        answer = "No people-related notes found." if not results else "People-related notes I found."
        return results, answer, 0.6 if results else 0.35

    def _handle_search(self, user, query_text: str, timeframe: Optional[Dict[str, str]]):
        entity_terms = self._extract_entities(query_text)
        q = Q(title__icontains=query_text) | Q(content__icontains=query_text) | Q(tags__icontains=query_text)
        for term in entity_terms:
            q |= Q(title__icontains=term) | Q(content__icontains=term) | Q(tags__icontains=term)
        queryset = Item.objects.filter(user=user).filter(q).order_by("-created_at")[:MAX_RESULTS]
        items = list(queryset)

        # Optional: boost similarity if embeddings available
        query_embedding = self.embedding_service.embed_text(query_text)
        results: List[Dict[str, Any]] = []
        for item in items:
            score = 0.5
            if query_embedding:
                item_embedding = self.embedding_service.embed_text(item.content or item.title)
                if item_embedding:
                    score = self.embedding_service.compute_similarity(query_embedding, item_embedding)
            results.append(self._item_to_result(item, score=score))

        answer = "No results found." if not results else "Here are the most relevant items I found."
        best_score = max((r.get("score", 0.0) for r in results), default=0.0)
        return results, answer, float(best_score)

    def _collection_to_result(self, collection: SmartCollection) -> Dict[str, Any]:
        return {
            "type": "smart_collection",
            "id": collection.id,
            "name": collection.name,
            "category": collection.category,
            "confidence": collection.confidence_score,
            "url": f"/api/knowledge-graph/smart-collections/{collection.id}/",
        }

    def _item_to_result(self, item: Item, score: float) -> Dict[str, Any]:
        snippet = (item.content or "")[:240]
        return {
            "type": "item",
            "id": item.id,
            "title": item.title,
            "item_type": item.item_type,
            "score": round(float(score), 3),
            "snippet": snippet,
            "tags": item.tags,
            "url": f"/api/items/{item.id}/",
        }

    def _extract_entities(self, query_text: str) -> List[str]:
        # Simple heuristic: capture quoted phrases and capitalized tokens
        entities: List[str] = []
        entities.extend(re.findall(r'"([^"]+)"', query_text))
        for word in query_text.split():
            if word.istitle() and len(word) > 2:
                entities.append(word)
        # Deduplicate while preserving order
        seen = set()
        deduped = []
        for e in entities:
            if e not in seen:
                seen.add(e)
                deduped.append(e)
        return deduped

    def _to_dt(self, value: str) -> Optional[datetime]:
        try:
            return datetime.fromisoformat(value)
        except Exception:
            return None
