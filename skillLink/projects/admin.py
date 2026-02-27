from django.contrib import admin
from .models import Project, Bid, Escrow, WorkCompletion, Review, Payment

class BidInline(admin.TabularInline):
    model = Bid
    extra = 0

class ReviewInline(admin.TabularInline):
    model = Review
    extra = 0

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['title', 'client', 'freelancer', 'status', 'budget', 'payment_status', 'created_at']
    list_filter = ['status', 'payment_status', 'created_at']
    search_fields = ['title', 'description', 'client__username', 'freelancer__username']
    readonly_fields = ['created_at', 'updated_at', 'completed_at']
    inlines = [BidInline, ReviewInline]
    fieldsets = (
        ('Project Details', {
            'fields': ('title', 'description', 'budget', 'client', 'freelancer')
        }),
        ('Status', {
            'fields': ('status', 'payment_status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = ['project', 'freelancer', 'amount', 'status', 'work_status', 'created_at']
    list_filter = ['status', 'work_status', 'created_at']
    search_fields = ['project__title', 'freelancer__username']
    readonly_fields = ['created_at', 'updated_at', 'submitted_at', 'accepted_at']
    fieldsets = (
        ('Bid Details', {
            'fields': ('project', 'freelancer', 'amount', 'delivery_days', 'proposal')
        }),
        ('Status', {
            'fields': ('status', 'work_status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'submitted_at', 'accepted_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Escrow)
class EscrowAdmin(admin.ModelAdmin):
    list_display = ['project', 'amount', 'status', 'created_at', 'released_at']
    list_filter = ['status', 'created_at']
    search_fields = ['project__title', 'transaction_id']
    readonly_fields = ['created_at', 'held_at', 'released_at']
    fieldsets = (
        ('Escrow Details', {
            'fields': ('project', 'bid', 'amount', 'status')
        }),
        ('Transaction', {
            'fields': ('transaction_id', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'held_at', 'released_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(WorkCompletion)
class WorkCompletionAdmin(admin.ModelAdmin):
    list_display = ['project', 'status', 'submitted_at', 'approved_at', 'revision_count']
    list_filter = ['status', 'submitted_at']
    search_fields = ['project__title', 'bid__freelancer__username']
    readonly_fields = ['submitted_at', 'reviewed_at', 'approved_at']
    fieldsets = (
        ('Submission', {
            'fields': ('project', 'bid', 'submission_notes', 'submission_files_link', 'submitted_at')
        }),
        ('Review', {
            'fields': ('status', 'review_notes', 'revision_count', 'reviewed_at')
        }),
        ('Approval', {
            'fields': ('approved_at',),
            'classes': ('collapse',)
        }),
    )

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['reviewer', 'reviewee', 'rating', 'project', 'review_type', 'created_at']
    list_filter = ['rating', 'review_type', 'created_at']
    search_fields = ['project__title', 'reviewer__username', 'reviewee__username']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Review Details', {
            'fields': ('project', 'bid', 'reviewer', 'reviewee', 'review_type')
        }),
        ('Ratings', {
            'fields': ('rating', 'quality', 'communication', 'professionalism', 'timeliness')
        }),
        ('Content', {
            'fields': ('title', 'comment')
        }),
        ('Verification', {
            'fields': ('is_verified_purchase',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['get_project', 'payer', 'payee', 'amount', 'status', 'payment_method', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['project__title', 'payer__username', 'payee__username', 'transaction_id', 'reference_number']
    readonly_fields = ['created_at', 'initiated_at', 'completed_at', 'reference_number']
    fieldsets = (
        ('Payment Details', {
            'fields': ('project', 'bid', 'amount', 'currency', 'payment_method')
        }),
        ('Parties', {
            'fields': ('payer', 'payee')
        }),
        ('Fees & Amount', {
            'fields': ('platform_fee', 'net_amount')
        }),
        ('Status & Transaction', {
            'fields': ('status', 'transaction_id', 'reference_number')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'initiated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
        ('Error Info', {
            'fields': ('error_message', 'notes'),
            'classes': ('collapse',)
        }),
    )
    
    def get_project(self, obj):
        return obj.project.title
    get_project.short_description = 'Project'
