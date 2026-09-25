from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .serializers import NotificationSerializer
from apps.notifications.models import Notification
from rest_framework.permissions import IsAuthenticatedOrReadOnly

class NotificationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for notifications
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        # Return recent notifications for current user
        return Notification.objects.filter(
            user=self.request.user,
            created_at__gte=timezone.now() - timezone.timedelta(days=30)
        ).order_by('-created_at')
    
    @action(detail=False, methods=['get'])
    def unread(self, request):
        """Get unread notifications"""
        queryset = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).order_by('-created_at')[:10]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['patch'])
    def mark_read(self, request, pk=None):
        """Mark notification as read"""
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        serializer = self.get_serializer(notification)
        return Response(serializer.data)
