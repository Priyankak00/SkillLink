from django.db.models.signals import post_save
from django.dispatch import receiver
from projects.models import Project
from .models import ChatRoom

@receiver(post_save, sender=Project)
def create_private_chat_room(sender, instance, **kwargs):
    # If the project status changes to in_progress and has a freelancer
    if instance.status == 'in_progress' and instance.freelancer:
        # get_or_create ensures we don't create duplicate rooms
        ChatRoom.objects.get_or_create(project=instance)