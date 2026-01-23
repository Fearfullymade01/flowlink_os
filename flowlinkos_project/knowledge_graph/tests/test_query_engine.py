import datetime
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone

from api.models import Item
from knowledge_graph.models import SmartCollection
from knowledge_graph.query_engine import QueryRouter


class QueryEngineTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="pass")
        self.router = QueryRouter()

    def test_parse_timeframe_next_week(self):
        timeframe = self.router._parse_timeframe("What did I plan for next week?")
        self.assertIsNotNone(timeframe)
        self.assertEqual(timeframe.get("label"), "next_week")
        self.assertLess(timeframe["start"], timeframe["end"])

    def test_parse_timeframe_absolute_date(self):
        timeframe = self.router._parse_timeframe("Show notes on 2026-01-23")
        self.assertIsNotNone(timeframe)
        self.assertEqual(timeframe.get("label"), "date")

    def test_item_result_has_deep_link(self):
        item = Item.objects.create(
            user=self.user,
            source=None,
            item_type="note",
            title="Test note",
            content="Some content",
            metadata={},
            tags="",
            is_archived=False,
            priority=0,
        )
        result = self.router._item_to_result(item, score=0.8)
        self.assertEqual(result.get("url"), f"/api/items/{item.id}/")

    def test_collection_result_has_deep_link(self):
        collection = SmartCollection.objects.create(
            user=self.user,
            name="Project Alpha",
            category="project",
            description="",
            confidence_score=0.9,
            item_count=0,
        )
        result = self.router._collection_to_result(collection)
        self.assertEqual(
            result.get("url"),
            f"/api/knowledge-graph/smart-collections/{collection.id}/",
        )

    def test_low_confidence_falls_back_to_search(self):
        def fake_projects(self_obj, user, query_text, timeframe):
            return [], "projects empty", 0.1

        def fake_search(self_obj, user, query_text, timeframe):
            return [
                {"type": "item", "id": 123, "title": "A", "score": 0.5}
            ], "search answer", 0.5

        # Force low intent confidence and empty project results
        self.router.classifier.classify = lambda text: ("projects", 0.1)
        self.router._handle_projects = fake_projects.__get__(self.router)
        self.router._handle_search = fake_search.__get__(self.router)

        result = self.router.execute(self.user, "something uncertain")
        self.assertTrue(result.get("fallback"))
        self.assertEqual(result.get("intent"), "search")
        self.assertEqual(len(result.get("results", [])), 1)
