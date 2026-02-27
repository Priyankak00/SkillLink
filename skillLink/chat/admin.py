from django.contrib import admin
from .models import ChatRoom, Message

@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ['project', 'created_at']
    search_fields = ['project__title']

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'room', 'timestamp']
    search_fields = ['sender__username', 'room__project__title']
    ordering = ['-timestamp']
