from celery import shared_task
from django.core.mail import send_mail
from django.contrib.auth import get_user_model

@shared_task
def send_welcome_email_task(user_id):
    User = get_user_model()
    try:
        user = User.objects.get(pk=user_id)
        subject = 'Welcome to SkillLink!'
        message = f'Hi {user.username}, thanks for joining the best marketplace for pros.'
        
        send_mail(
            subject,
            message,
            'support@skilllink.com',
            [user.email],
            fail_silently=False,
        )
        return f"Email sent to {user.email}"
    except User.DoesNotExist:
        return "User not found"