from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import ChatRoom, Message
from projects.models import Project
from .serializers import MessageSerializer


class ChatRoomListAPIView(generics.ListAPIView):
    """Get or create chat room for a project"""
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        project_id = self.kwargs.get('project_id')
        project = get_object_or_404(Project, id=project_id)
        
        # Only client and freelancer can access chat
        if self.request.user not in [project.client, project.freelancer]:
            return Message.objects.none()
        
        # Get or create chat room
        chat_room, _ = ChatRoom.objects.get_or_create(project=project)
        return chat_room.messages.all().order_by('-timestamp')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class SendMessageAPIView(generics.CreateAPIView):
    """Send a message in project chat"""
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        project_id = self.kwargs.get('project_id')
        project = get_object_or_404(Project, id=project_id)
        
        # Only client and freelancer can send messages
        if request.user not in [project.client, project.freelancer]:
            return Response(
                {'detail': 'Only project client and freelancer can send messages.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Project must have a freelancer assigned (accepted project)
        if not project.freelancer:
            return Response(
                {'detail': 'Cannot chat on projects without an accepted freelancer.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get or create chat room
        chat_room, _ = ChatRoom.objects.get_or_create(project=project)
        
        # Create message
        message = Message.objects.create(
            room=chat_room,
            sender=request.user,
            content=request.data.get('content', '')
        )
        
        serializer = self.get_serializer(message)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

