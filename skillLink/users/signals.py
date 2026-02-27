from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.db import transaction
import logging

try:
    from .tasks import send_welcome_email_task
    CELERY_AVAILABLE = True
except Exception as e:
    CELERY_AVAILABLE = False
    logging.warning(f"Celery tasks not available: {e}")

User = get_user_model()

@receiver(post_save, sender=User)
def trigger_welcome_email(sender, instance, created, **kwargs):
    if created and CELERY_AVAILABLE:
        # Schedule the task after the DB transaction finishes
        try:
            transaction.on_commit(
                lambda: send_welcome_email_task.delay(instance.id)
            )
        except Exception as e:
            # Log error but don't prevent user creation
            logging.error(f"Failed to queue welcome email: {e}")


        