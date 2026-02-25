from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.db import transaction
from .tasks import send_welcome_email_task

User = get_user_model()

@receiver(post_save, sender=User)
def trigger_welcome_email(sender, instance, created, **kwargs):
    if created:
        # Schedule the task after the DB transaction finishes
        
        transaction.on_commit(
            lambda: send_welcome_email_task.delay(instance.id)
        )


        