from django import forms
from django.core.exceptions import ValidationError
from .models import Bid, WorkCompletion, Review, Payment


class WorkSubmissionForm(forms.ModelForm):
    submission_notes = forms.CharField(
        label='Work Completion Notes',
        widget=forms.Textarea(attrs={
            'placeholder': 'Describe what you\'ve completed, any important notes, deliverables included...',
            'rows': 8,
            'class': 'form-control'
        }),
        help_text='Provide details about your completed work'
    )
    
    submission_files_link = forms.URLField(
        label='Link to Delivered Files',
        required=False,
        widget=forms.URLInput(attrs={
            'placeholder': 'https://drive.google.com/drive/folders/...',
            'class': 'form-control'
        }),
        help_text='Provide a link to your files (Google Drive, Dropbox, GitHub, etc.)'
    )
    
    class Meta:
        model = WorkCompletion
        fields = ['submission_notes', 'submission_files_link']


class WorkReviewForm(forms.ModelForm):
    REVIEW_CHOICES = [
        ('approved', 'Approve - Work is Complete'),
        ('revision_requested', 'Request Revision'),
    ]
    
    action = forms.ChoiceField(
        choices=REVIEW_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label='Action'
    )
    
    review_notes = forms.CharField(
        label='Feedback / Revision Notes',
        widget=forms.Textarea(attrs={
            'placeholder': 'If requesting revisions, please specify what needs to be changed...',
            'rows': 8,
            'class': 'form-control'
        }),
        required=False,
        help_text='Your feedback or any revisions needed'
    )
    
    class Meta:
        model = WorkCompletion
        fields = []


class ReviewForm(forms.ModelForm):
    RATING_CHOICES = [
        (1, '1 - Poor'),
        (2, '2 - Fair'),
        (3, '3 - Good'),
        (4, '4 - Very Good'),
        (5, '5 - Excellent'),
    ]
    
    rating = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label='Overall Rating'
    )
    
    quality = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Quality of Work',
        required=False
    )
    
    communication = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Communication',
        required=False
    )
    
    professionalism = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Professionalism',
        required=False
    )
    
    timeliness = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Timeliness',
        required=False
    )
    
    title = forms.CharField(
        label='Review Title',
        max_length=255,
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g., "Excellent work, would hire again!"',
            'class': 'form-control'
        })
    )
    
    comment = forms.CharField(
        label='Review Details',
        widget=forms.Textarea(attrs={
            'placeholder': 'Share your experience working on this project...',
            'rows': 8,
            'class': 'form-control'
        }),
        help_text='Detailed feedback helps build our community\'s trust'
    )
    
    class Meta:
        model = Review
        fields = ['rating', 'quality', 'communication', 'professionalism', 'timeliness', 'title', 'comment']
    
    def clean(self):
        cleaned_data = super().clean()
        rating = cleaned_data.get('rating')
        if rating:
            cleaned_data['rating'] = int(rating)
        
        quality = cleaned_data.get('quality')
        if quality:
            cleaned_data['quality'] = int(quality)
        
        communication = cleaned_data.get('communication')
        if communication:
            cleaned_data['communication'] = int(communication)
        
        professionalism = cleaned_data.get('professionalism')
        if professionalism:
            cleaned_data['professionalism'] = int(professionalism)
        
        timeliness = cleaned_data.get('timeliness')
        if timeliness:
            cleaned_data['timeliness'] = int(timeliness)
        
        return cleaned_data


class PaymentForm(forms.ModelForm):
    PAYMENT_METHOD_CHOICES = [
        ('card', 'Credit/Debit Card'),
        ('wallet', 'Use SkillLink Wallet Balance'),
        ('bank_transfer', 'Bank Transfer'),
    ]
    
    payment_method = forms.ChoiceField(
        choices=PAYMENT_METHOD_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label='Payment Method'
    )
    
    notes = forms.CharField(
        label='Payment Notes (Optional)',
        widget=forms.Textarea(attrs={
            'placeholder': 'Any special instructions...',
            'rows': 4,
            'class': 'form-control'
        }),
        required=False,
        help_text='Add any special instructions or notes for this payment'
    )
    
    class Meta:
        model = Payment
        fields = ['payment_method', 'notes']


class QuickApproveForm(forms.Form):
    confirm = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='I confirm that the work meets my requirements and I approve this project for payment'
    )
