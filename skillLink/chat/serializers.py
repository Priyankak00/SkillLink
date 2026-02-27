from rest_framework import serializers
from .models import ChatRoom, Message

class MessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    sender_id = serializers.IntegerField(source='sender.id', read_only=True)
    room_id = serializers.IntegerField(source='room.id', read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'room_id', 'sender_id', 'sender_username', 'content', 'timestamp']
        read_only_fields = ['id', 'sender_id', 'sender_username', 'room_id', 'timestamp']


class ChatRoomSerializer(serializers.ModelSerializer):
    project_id = serializers.IntegerField(source='project.id', read_only=True)
    project_title = serializers.CharField(source='project.title', read_only=True)
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = ChatRoom
        fields = ['id', 'project_id', 'project_title', 'created_at', 'messages']
        read_only_fields = ['id', 'created_at', 'messages']

