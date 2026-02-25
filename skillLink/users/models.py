from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    IS_FREELANCER = 'freelancer'
    IS_CLIENT = 'client'
    
    ROLE_CHOICES = (
        (IS_FREELANCER, 'Freelancer'),
        (IS_CLIENT, 'Client'),
    )
    
    CATEGORY_CHOICES = (
        ('designer', 'Designer (UI/UX, Graphic, etc.)'),
        ('developer', 'Developer (Web, Mobile, Backend)'),
        ('writer', 'Writer (Content, Blog, Copy)'),
        ('marketer', 'Marketer (Digital, Social, SEO)'),
        ('translator', 'Translator'),
        ('consultant', 'Consultant & Specialist'),
        ('other', 'Other'),
    )
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=IS_CLIENT)
    title = models.CharField(max_length=255, blank=True, null=True)  # Professional title
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    skills = models.JSONField(default=list, blank=True)  # Store skills as JSON array
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.role})"