from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import UserProfile, Source, Workflow


class UserProfileViewSet(viewsets.ViewSet):
    """ViewSet for user profile management."""
    permission_classes = [IsAuthenticated]
    
    def retrieve(self, request):
        """Get current user's profile."""
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        return Response({
            'id': profile.id,
            'bio': profile.bio,
            'timezone': profile.timezone,
            'is_verified': profile.is_verified,
            'created_at': profile.created_at,
        })


def home(request):
    """Home page view."""
    return render(request, 'index.html')
