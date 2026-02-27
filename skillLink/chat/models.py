from django.db import models
from django.conf import settings
from projects.models import Project

class ChatRoom(models.Model):
    # One project = One chat room between the client and the winning freelancer
    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name='chat_room')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Chat for Project: {self.project.title}"

class Message(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.sender.username}: {self.content[:20]}"


class AuctionItem(models.Model):
    title = models.CharField(max_length=255)
    current_price = models.DecimalField(max_digits=10, decimal_places=2)
    highest_bidder = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="winning_auctions",
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.title} - {self.current_price}"