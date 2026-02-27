from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count, Q, Avg
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from uuid import uuid4
from rest_framework import generics, permissions, serializers, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from .models import Project, Bid, Escrow, WorkCompletion, Review, Payment
from .serializers import ProjectSerializer, BidSerializer
from .permissions import IsFreelancer
from .forms import WorkSubmissionForm, WorkReviewForm, ReviewForm, PaymentForm, QuickApproveForm
from chat.models import ChatRoom


class MarketplaceView(LoginRequiredMixin, ListView):
    template_name = 'projects/marketplace.html'
    context_object_name = 'projects'
    paginate_by = 12

    def get_queryset(self):
        return Project.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_projects'] = Project.objects.count()
        context['open_projects'] = Project.objects.filter(status='open').count()
        return context


class ProjectListView(ListView):
    model = Project
    template_name = 'projects/project_list.html'
    context_object_name = 'projects'
    paginate_by = 12

    def get_queryset(self):
        queryset = Project.objects.all().order_by('-created_at').annotate(
            bid_count=Count('bids')
        )
        
        status_filter = self.request.GET.get('status')
        if status_filter in ['open', 'in_progress', 'completed']:
            queryset = queryset.filter(status=status_filter)
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )
        
        min_budget = self.request.GET.get('min_budget')
        max_budget = self.request.GET.get('max_budget')
        if min_budget:
            queryset = queryset.filter(budget__gte=min_budget)
        if max_budget:
            queryset = queryset.filter(budget__lte=max_budget)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_projects'] = Project.objects.count()
        context['open_projects'] = Project.objects.filter(status='open').count()
        context['active_projects'] = Project.objects.filter(status='in_progress').count()
        return context


class ProjectDetailView(DetailView):
    model = Project
    template_name = 'projects/project_detail.html'
    context_object_name = 'project'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_object()
        context['bids'] = project.bids.filter(status='pending').order_by('-created_at')
        context['accepted_bids'] = project.bids.filter(status='accepted').order_by('-created_at')
        context['declined_bids'] = project.bids.filter(status='rejected').order_by('-created_at')
        context['user_has_bid'] = False
        context['can_bid'] = False
        
        if self.request.user.is_authenticated:
            context['user_has_bid'] = project.bids.filter(
                freelancer=self.request.user
            ).exists()
            context['can_bid'] = (
                self.request.user != project.client and 
                project.status == 'open' and 
                not context['user_has_bid']
            )
        
        return context


class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    template_name = 'projects/project_form.html'
    fields = ['title', 'description', 'budget']
    success_url = reverse_lazy('projects:project-list')

    def form_valid(self, form):
        form.instance.client = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, 'Project posted successfully!')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Post a New Project'
        context['button_text'] = 'Post Project'
        return context


class ProjectUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Project
    template_name = 'projects/project_form.html'
    fields = ['title', 'description', 'status']
    success_url = reverse_lazy('projects:project-list')

    def test_func(self):
        project = self.get_object()
        return self.request.user == project.client

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Edit Project'
        context['button_text'] = 'Update Project'
        return context


class ProjectDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Project
    success_url = reverse_lazy('projects:my-projects')
    
    def test_func(self):
        project = self.get_object()
        return self.request.user == project.client
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Project deleted successfully!')
        return super().delete(request, *args, **kwargs)


class MyProjectsView(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'projects/my_projects.html'
    context_object_name = 'projects'
    paginate_by = 10

    def get_queryset(self):
        if self.request.user.role == 'client':
            return Project.objects.filter(client=self.request.user).annotate(
                bid_count=Count('bids')
            ).order_by('-created_at')
        else:
            return Project.objects.filter(
                Q(client=self.request.user) | Q(freelancer=self.request.user)
            ).distinct().order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['role'] = self.request.user.role
        if self.request.user.role == 'client':
            context['open'] = Project.objects.filter(
                client=self.request.user, status='open'
            ).count()
            context['active'] = Project.objects.filter(
                client=self.request.user, status='in_progress'
            ).count()
            context['completed'] = Project.objects.filter(
                client=self.request.user, status='completed'
            ).count()
        else:
            context['posted'] = Project.objects.filter(
                client=self.request.user
            ).count()
            context['accepted'] = Project.objects.filter(
                freelancer=self.request.user
            ).count()
            context['active'] = Project.objects.filter(
                Q(client=self.request.user) | Q(freelancer=self.request.user), 
                status='in_progress'
            ).count()
            context['completed'] = Project.objects.filter(
                Q(client=self.request.user) | Q(freelancer=self.request.user), 
                status='completed'
            ).count()
        return context


class BidCreateFormView(LoginRequiredMixin, CreateView):
    model = Bid
    fields = ['amount', 'delivery_days', 'proposal']
    template_name = 'projects/project_detail.html'
    success_url = reverse_lazy('projects:my-projects')

    def form_valid(self, form):
        project = get_object_or_404(Project, pk=self.kwargs.get('project_pk'))
        
        if project.status != 'open':
            messages.error(self.request, "This project is no longer accepting bids.")
            return redirect('projects:project-detail', pk=project.pk)
        
        if project.client == self.request.user:
            messages.error(self.request, "You cannot bid on your own project.")
            return redirect('projects:project-detail', pk=project.pk)
        
        if Bid.objects.filter(project=project, freelancer=self.request.user).exists():
            messages.error(self.request, "You have already placed a bid on this project.")
            return redirect('projects:project-detail', pk=project.pk)
        
        form.instance.project = project
        form.instance.freelancer = self.request.user
        messages.success(self.request, "Your bid has been submitted successfully!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Please correct the errors below.")
        return redirect('projects:project-detail', pk=self.kwargs.get('project_pk'))


class ProjectCreateAPIView(generics.CreateAPIView):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(client=self.request.user)


class AvailableProjectsListView(generics.ListAPIView):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'budget']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'budget', 'bid_count']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = Project.objects.filter(status='open').annotate(
            bid_count=Count('bids')
        ).order_by('-created_at')
        
        if self.request.user.is_authenticated:
            queryset = queryset.exclude(client=self.request.user)
        
        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class ProjectDetailAPIView(generics.RetrieveAPIView):
    queryset = Project.objects.all().annotate(bid_count=Count('bids'))
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['include_bids'] = True
        return context


class BidCreateView(generics.CreateAPIView):
    serializer_class = BidSerializer
    permission_classes = [permissions.IsAuthenticated, IsFreelancer]

    def get_queryset(self):
        return Bid.objects.none()

    def perform_create(self, serializer):
        project_id = self.kwargs.get('project_id')
        project = get_object_or_404(Project, id=project_id)

        if project.status != 'open':
            raise serializers.ValidationError("This project is no longer accepting bids.")

        if project.client == self.request.user:
            raise serializers.ValidationError("You cannot bid on your own project.")

        if Bid.objects.filter(project=project, freelancer=self.request.user).exists():
            raise serializers.ValidationError("You have already placed a bid on this project.")

        serializer.save(freelancer=self.request.user, project=project)

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except serializers.ValidationError as e:
            return Response(
                {'detail': str(e.detail[0]) if e.detail else 'Validation error'},
                status=status.HTTP_400_BAD_REQUEST
            )


class BidListView(generics.ListAPIView):
    serializer_class = BidSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        project_id = self.kwargs.get('project_id')
        project = get_object_or_404(Project, id=project_id)
        
        if self.request.user != project.client:
            return Bid.objects.none()
        
        return Bid.objects.filter(project=project).order_by('-created_at')


class UserBidsListView(generics.ListAPIView):
    serializer_class = BidSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Bid.objects.filter(freelancer=self.request.user).order_by('-created_at')


class BidAcceptView(generics.UpdateAPIView):
    serializer_class = BidSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Bid.objects.all()
    
    def update(self, request, *args, **kwargs):
        bid = self.get_object()
        project = bid.project
        
        if project.client != request.user:
            return Response(
                {'detail': 'Only the project owner can accept bids.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        project.freelancer = bid.freelancer
        project.status = 'in_progress'
        project.save()
        
        ChatRoom.objects.get_or_create(project=project)
        
        Bid.objects.filter(project=project).exclude(id=bid.id).update(status='rejected')
        
        bid.status = 'accepted'
        bid.save()
        
        serializer = self.get_serializer(bid)
        return Response(serializer.data)


class BidRejectView(generics.UpdateAPIView):
    serializer_class = BidSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Bid.objects.all()
    
    def update(self, request, *args, **kwargs):
        bid = self.get_object()
        project = bid.project
        
        if project.client != request.user:
            return Response(
                {'detail': 'Only the project owner can reject bids.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        bid.status = 'rejected'
        bid.save()
        
        serializer = self.get_serializer(bid)
        return Response(serializer.data)


class SubmitWorkView(LoginRequiredMixin, FormView):
    form_class = WorkSubmissionForm
    template_name = 'projects/submit_work.html'
    
    def get_project_and_bid(self):
        project_id = self.kwargs.get('project_id')
        project = get_object_or_404(Project, id=project_id)
        bid = get_object_or_404(Bid, project=project, status='accepted')
        return project, bid
    
    def test_freelancer_permission(self):
        project, bid = self.get_project_and_bid()
        return self.request.user == bid.freelancer
    
    def dispatch(self, request, *args, **kwargs):
        if not self.test_freelancer_permission():
            messages.error(request, "You don't have permission to submit work on this project.")
            return redirect('projects:project-list')
        
        project, _ = self.get_project_and_bid()
        if project.status not in ['in_progress']:
            messages.error(request, "This project is not in progress.")
            return redirect('projects:project-detail', pk=project.id)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project, bid = self.get_project_and_bid()
        context['project'] = project
        context['bid'] = bid
        
        try:
            context['existing_work'] = WorkCompletion.objects.get(bid=bid)
        except WorkCompletion.DoesNotExist:
            context['existing_work'] = None
        
        return context
    
    def form_valid(self, form):
        project, bid = self.get_project_and_bid()
        
        work_completion, created = WorkCompletion.objects.get_or_create(
            bid=bid,
            defaults={'project': project}
        )
        
        work_completion.submission_notes = form.cleaned_data['submission_notes']
        work_completion.submission_files_link = form.cleaned_data['submission_files_link']
        work_completion.status = 'pending'
        work_completion.save()
        
        bid.work_status = 'submitted'
        bid.submitted_at = timezone.now()
        bid.save()
        
        project.status = 'work_submitted'
        project.save()
        
        messages.success(self.request, 'Your work has been submitted! The client will review it shortly.')
        return redirect('projects:project-detail', pk=project.id)


class ReviewWorkView(LoginRequiredMixin, FormView):
    form_class = WorkReviewForm
    template_name = 'projects/review_work.html'
    
    def get_work_completion(self):
        project_id = self.kwargs.get('project_id')
        project = get_object_or_404(Project, id=project_id)
        work_completion = get_object_or_404(WorkCompletion, project=project)
        return project, work_completion
    
    def test_client_permission(self):
        project, _ = self.get_work_completion()
        return self.request.user == project.client
    
    def dispatch(self, request, *args, **kwargs):
        if not self.test_client_permission():
            messages.error(request, "You don't have permission to review this work.")
            return redirect('projects:project-list')
        
        project, work = self.get_work_completion()
        if project.status != 'work_submitted':
            messages.error(request, "No submitted work to review for this project.")
            return redirect('projects:project-detail', pk=project.id)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project, work_completion = self.get_work_completion()
        context['project'] = project
        context['work'] = work_completion
        return context
    
    def form_valid(self, form):
        project, work_completion = self.get_work_completion()
        action = form.cleaned_data['action']
        review_notes = form.cleaned_data.get('review_notes', '')
        
        if action == 'approved':
            work_completion.status = 'approved'
            work_completion.approved_at = timezone.now()
            work_completion.reviewed_at = timezone.now()
            work_completion.review_notes = review_notes
            work_completion.save()
            
            bid = work_completion.bid
            bid.work_status = 'completed'
            bid.accepted_at = timezone.now()
            bid.save()
            
            project.status = 'completed'
            project.completed_at = timezone.now()
            project.payment_status = 'escrowed'
            project.save()
            
            messages.success(self.request, 'Work approved! You can now proceed with payment.')
            return redirect('projects:initiate-payment', project_id=project.id)
        
        elif action == 'revision_requested':
            work_completion.status = 'revision_requested'
            work_completion.reviewed_at = timezone.now()
            work_completion.review_notes = review_notes
            work_completion.revision_count += 1
            work_completion.save()
            
            bid = work_completion.bid
            bid.work_status = 'revision_requested'
            bid.save()
            
            project.status = 'in_progress'
            project.save()
            
            messages.success(self.request, 'Revision request sent to the freelancer.')
            return redirect('projects:project-detail', pk=project.id)


class InitiatePaymentView(LoginRequiredMixin, FormView):
    form_class = PaymentForm
    template_name = 'projects/initiate_payment.html'
    
    def get_project(self):
        project_id = self.kwargs.get('project_id')
        return get_object_or_404(Project, id=project_id)
    
    def test_client_permission(self):
        project = self.get_project()
        return self.request.user == project.client
    
    def dispatch(self, request, *args, **kwargs):
        if not self.test_client_permission():
            messages.error(request, "You don't have permission to process payment for this project.")
            return redirect('projects:project-list')
        
        project = self.get_project()
        if project.status != 'completed':
            messages.error(request, "This project is not ready for payment.")
            return redirect('projects:project-detail', pk=project.id)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_project()
        bid = project.bids.filter(status='accepted').first()
        
        context['project'] = project
        context['bid'] = bid
        context['amount'] = bid.amount if bid else 0
        context['platform_fee'] = bid.amount * 0.10 if bid else 0
        context['net_amount'] = bid.amount * 0.90 if bid else 0
        
        return context
    
    def form_valid(self, form):
        project = self.get_project()
        bid = project.bids.filter(status='accepted').first()
        
        payment = Payment.objects.create(
            project=project,
            bid=bid,
            payer=self.request.user,
            payee=project.freelancer,
            amount=bid.amount,
            payment_method=form.cleaned_data['payment_method'],
            notes=form.cleaned_data.get('notes', '')
        )
        
        payment.calculate_net_amount()
        payment.reference_number = f"SKL-{uuid4().hex[:8].upper()}"
        payment.status = 'processing'
        payment.initiated_at = timezone.now()
        payment.save()
        
        payment.status = 'completed'
        payment.completed_at = timezone.now()
        payment.transaction_id = f"TXN-{uuid4().hex[:12].upper()}"
        payment.save()
        
        project.payment_status = 'released'
        project.save()
        
        messages.success(self.request, f'Payment of ${payment.amount} successfully processed! The freelancer has been notified.')
        return redirect('projects:write-review', project_id=project.id)


class WriteReviewView(LoginRequiredMixin, FormView):
    form_class = ReviewForm
    template_name = 'projects/write_review.html'
    
    def get_project(self):
        project_id = self.kwargs.get('project_id')
        return get_object_or_404(Project, id=project_id)
    
    def dispatch(self, request, *args, **kwargs):
        project = self.get_project()
        
        if request.user not in [project.client, project.freelancer]:
            messages.error(request, "You don't have permission to review this project.")
            return redirect('projects:project-list')
        
        if project.status != 'completed' or project.payment_status != 'released':
            messages.error(request, "Payment must be completed before writing a review.")
            return redirect('projects:project-detail', pk=project.id)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_project()
        bid = project.bids.filter(status='accepted').first()
        
        context['project'] = project
        context['bid'] = bid
        
        if self.request.user == project.client:
            context['review_type'] = 'client_to_freelancer'
            context['reviewee'] = project.freelancer
            context['title_hint'] = f"Review of {project.freelancer.first_name}"
        else:
            context['review_type'] = 'freelancer_to_client'
            context['reviewee'] = project.client
            context['title_hint'] = f"Review of {project.client.first_name}"
        
        existing_review = Review.objects.filter(
            project=project,
            reviewer=self.request.user
        ).first()
        
        context['has_reviewed'] = existing_review is not None
        
        return context
    
    def form_valid(self, form):
        project = self.get_project()
        bid = project.bids.filter(status='accepted').first()
        
        if self.request.user == project.client:
            reviewee = project.freelancer
            review_type = 'client_to_freelancer'
        else:
            reviewee = project.client
            review_type = 'freelancer_to_client'
        
        review, created = Review.objects.get_or_create(
            project=project,
            reviewer=self.request.user,
            defaults={
                'bid': bid,
                'reviewee': reviewee,
                'review_type': review_type,
                'is_verified_purchase': True,
                'rating': form.cleaned_data['rating'],
                'quality': form.cleaned_data.get('quality'),
                'communication': form.cleaned_data.get('communication'),
                'professionalism': form.cleaned_data.get('professionalism'),
                'timeliness': form.cleaned_data.get('timeliness'),
                'title': form.cleaned_data['title'],
                'comment': form.cleaned_data['comment'],
            }
        )
        
        if not created:
            review.rating = form.cleaned_data['rating']
            review.quality = form.cleaned_data.get('quality')
            review.communication = form.cleaned_data.get('communication')
            review.professionalism = form.cleaned_data.get('professionalism')
            review.timeliness = form.cleaned_data.get('timeliness')
            review.title = form.cleaned_data['title']
            review.comment = form.cleaned_data['comment']
            review.save()
        
        messages.success(self.request, 'Thank you for your review! It helps our community.')
        return redirect('projects:project-detail', pk=project.id)