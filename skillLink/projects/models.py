from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

class Project(models.Model):
    STATUS_CHOICES = (
        ('open', 'Open for Bidding'),
        ('in_progress', 'In Progress'),
        ('work_submitted', 'Work Submitted - Awaiting Review'),
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
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    payment_status = models.CharField(
        max_length=20,
        choices=[
            ('not_started', 'Not Started'),
            ('escrowed', 'Funds Held in Escrow'),
            ('released', 'Payment Released'),
            ('refunded', 'Refunded'),
        ],
        default='not_started'
    )

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']


class Bid(models.Model):
    BID_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
    )
    
    WORK_STATUS_CHOICES = (
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('submitted', 'Work Submitted'),
        ('revision_requested', 'Revision Requested'),
        ('completed', 'Completed & Paid'),
    )

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='bids')
    freelancer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bids_made')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    delivery_days = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    proposal = models.TextField()
    status = models.CharField(max_length=20, choices=BID_STATUS_CHOICES, default='pending')
    work_status = models.CharField(max_length=20, choices=WORK_STATUS_CHOICES, default='not_started')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('project', 'freelancer')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.freelancer.username} - {self.project.title} - {self.amount}"


class Escrow(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending - Awaiting Freelancer'),
        ('held', 'Held - Work Submitted'),
        ('released', 'Released - Payment Completed'),
        ('refunded', 'Refunded - Project Cancelled'),
    )
    
    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name='escrow')
    bid = models.OneToOneField(Bid, on_delete=models.CASCADE, related_name='escrow')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    held_at = models.DateTimeField(null=True, blank=True)
    released_at = models.DateTimeField(null=True, blank=True)
    transaction_id = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"Escrow - {self.project.title} - {self.amount} - {self.status}"
    
    class Meta:
        ordering = ['-created_at']


class WorkCompletion(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending Client Review'),
        ('revision_requested', 'Revision Requested'),
        ('approved', 'Approved & Complete'),
    )
    
    bid = models.OneToOneField(Bid, on_delete=models.CASCADE, related_name='work_completion')
    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name='work_completion')
    
    submitted_at = models.DateTimeField(auto_now_add=True)
    submission_notes = models.TextField(help_text="Freelancer's notes about the completed work")
    submission_files_link = models.URLField(blank=True, help_text="Link to submitted files (Google Drive, Dropbox, etc.)")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True, help_text="Client's feedback or revision requests")
    revision_count = models.PositiveIntegerField(default=0)
    
    approved_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Work Completion - {self.project.title} - {self.status}"
    
    class Meta:
        ordering = ['-submitted_at']


class Review(models.Model):
    TYPE_CHOICES = (
        ('client_to_freelancer', 'Client Review of Freelancer'),
        ('freelancer_to_client', 'Freelancer Review of Client'),
    )
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='reviews')
    bid = models.ForeignKey(Bid, on_delete=models.CASCADE, related_name='reviews')
    
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews_given')
    reviewee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews_received')
    
    review_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = models.CharField(max_length=255)
    comment = models.TextField()
    
    quality = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True)
    communication = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True)
    professionalism = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True)
    timeliness = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True)
    
    is_verified_purchase = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Review - {self.reviewer.username} -> {self.reviewee.username} - {self.rating}★"
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ('project', 'reviewer')


class Payment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )
    
    PAYMENT_METHOD_CHOICES = (
        ('card', 'Credit/Debit Card'),
        ('wallet', 'SkillLink Wallet'),
        ('bank_transfer', 'Bank Transfer'),
        ('paypal', 'PayPal'),
    )
    
    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name='payment')
    bid = models.OneToOneField(Bid, on_delete=models.CASCADE, related_name='payment')
    
    payer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='payments_made')
    payee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='payments_received')
    
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    currency = models.CharField(max_length=3, default='USD')
    
    platform_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="SkillLink platform fee")
    net_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)], help_text="Amount freelancer will receive after fees")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='card')
    
    transaction_id = models.CharField(max_length=255, blank=True, unique=True)
    reference_number = models.CharField(max_length=50, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)
    initiated_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    notes = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    
    def __str__(self):
        return f"Payment - {self.project.title} - {self.amount} - {self.status}"
    
    def calculate_net_amount(self):
        platform_fee_percentage = 0.10
        self.platform_fee = self.amount * platform_fee_percentage
        self.net_amount = self.amount - self.platform_fee
        return self.net_amount
    
    class Meta:
        ordering = ['-created_at']
