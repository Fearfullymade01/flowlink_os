"""
URL configuration for flowlinkos project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.views import home, query_ui

urlpatterns = [
    path('', home, name='home'),
    path('ask/', query_ui, name='query-ui'),
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('api/knowledge-graph/', include('knowledge_graph.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
