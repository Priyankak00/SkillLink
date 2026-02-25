from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
# Create your models here.

class Project(models.Model):
    STATUS_CHOICES = (
        ('open', 'Open for Bidding'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    title = models.CharField(max_length=255)
    description = models.TextField()
    budget = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(1.00)])
    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='projects_posted')
    freelancer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='projects_won')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Bid(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='bids')
    freelancer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bids_made')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_days = models.PositiveIntegerField()
    proposal = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # A freelancer can only bid ONCE per project
        unique_together = ('project', 'freelancer')

    def __str__(self):
        return f"{self.freelancer.username} - {self.amount}"
    
def accept_bid(self, bid):
    self.freelancer = bid.freelancer
    self.status = 'in_progress'
    self.save()
    # Logic for triggering a Celery notification would go here next!

