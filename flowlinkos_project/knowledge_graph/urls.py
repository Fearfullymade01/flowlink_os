from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'entities', views.EntityViewSet, basename='entity')
router.register(r'relationships', views.RelationshipViewSet, basename='relationship')
router.register(r'graph', views.GraphViewSet, basename='graph')

urlpatterns = [
    path('', include(router.urls)),
]
