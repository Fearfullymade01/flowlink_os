from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'entities', views.EntityViewSet, basename='entity')
router.register(r'relationships', views.RelationshipViewSet, basename='relationship')
router.register(r'entity-links', views.EntityItemLinkViewSet, basename='entity-item-link')
router.register(r'graph', views.GraphViewSet, basename='graph')
router.register(r'smart-collections', views.SmartCollectionViewSet, basename='smart-collection')

urlpatterns = [
    path('', include(router.urls)),
]
