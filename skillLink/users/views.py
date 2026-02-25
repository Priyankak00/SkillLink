from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth import get_user_model, login, logout
from django.db.models import Sum
from .serializers import RegisterSerializer, UserSerializer, LoginSerializer

User = get_user_model()


@api_view(['GET', 'POST'])
@permission_classes([permissions.AllowAny])
def register_view(request):
    """Register user via HTML form or API."""
    if request.method == 'GET':
        return render(request, 'users/register.html')

    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()

    login(request, user)
    token, created = Token.objects.get_or_create(user=user)

    if request.content_type and 'application/x-www-form-urlencoded' in request.content_type:
        if user.role == 'freelancer':
            return redirect('freelancer-dashboard')
        return redirect('client-dashboard')

    return Response({
        'token': token.key,
        'user': {
            'id': user.id,
            'email': user.email,
            'username': user.username,
            'role': getattr(user, 'role', 'client')
        },
        'message': 'Registration successful'
    }, status=status.HTTP_201_CREATED)


@api_view(['GET', 'POST'])
@permission_classes([permissions.AllowAny])
def login_view(request):
    """
    Authenticate user with email and password.
    POST - Login user and return token
    GET - Returns login form
    """
    if request.method == 'GET':
        return render(request, 'users/login.html')

    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user = serializer.validated_data['user']
    token, created = Token.objects.get_or_create(user=user)
    login(request, user)

    if request.content_type and 'application/x-www-form-urlencoded' in request.content_type:
        if user.role == 'freelancer':
            return redirect('freelancer-dashboard')
        return redirect('client-dashboard')

    return Response({
        'token': token.key,
        'user': {
            'id': user.id,
            'email': user.email,
            'username': user.username,
            'role': getattr(user, 'role', 'client')
        },
        'message': 'Login successful'
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    """
    Logout the authenticated user.
    POST - Logout user and invalidate token
    """
    try:
        Token.objects.get(user=request.user).delete()
    except Token.DoesNotExist:
        pass

    logout(request)

    return Response({
        'message': 'Logged out successfully'
    }, status=status.HTTP_200_OK)


@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([permissions.AllowAny])
def profile_view(request):
    """
    Retrieve and update user profile.
    GET - Returns HTML profile page or user data
    PUT/PATCH - Updates user profile
    """
    if request.method == 'GET':
        if request.accepted_renderer.format == 'html' or 'text/html' in request.META.get('HTTP_ACCEPT', ''):
            return render(request, 'users/profile.html', {
                'user': request.user if request.user.is_authenticated else None
            })

        if not request.user.is_authenticated:
            return Response(
                {"detail": "Authentication credentials were not provided."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    if not request.user.is_authenticated:
        return Response(
            {"detail": "Authentication credentials were not provided."},
            status=status.HTTP_403_FORBIDDEN
        )

    partial = request.method == 'PATCH'
    serializer = UserSerializer(request.user, data=request.data, partial=partial)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([permissions.IsAuthenticated])
def user_detail_view(request, pk):
    """
    CRUD operations for user accounts.
    GET - Retrieve specific user (CRUD - Read)
    PUT/PATCH - Update user (CRUD - Update)
    DELETE - Delete user account (CRUD - Delete)
    """
    user = get_object_or_404(User, pk=pk)
    if request.user != user and not request.user.is_staff:
        return Response(
            {"detail": "You can only access your own profile."},
            status=status.HTTP_403_FORBIDDEN
        )

    if request.method == 'GET':
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    if request.method in ['PUT', 'PATCH']:
        partial = request.method == 'PATCH'
        serializer = UserSerializer(user, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    user.delete()
    return Response(
        {"message": "User account deleted successfully"},
        status=status.HTTP_204_NO_CONTENT
    )


class DashboardRedirectView(LoginRequiredMixin, View):
    """
    Dashboard redirect view that sends users to their appropriate dashboard based on role.
    """
    login_url = 'login'
    
    def get(self, request, *args, **kwargs):
        """Redirect based on user role"""
        if request.user.role == 'freelancer':
            return redirect('freelancer-dashboard')
        else:
            return redirect('client-dashboard')


class FreelancerDashboardView(LoginRequiredMixin, TemplateView):
    """
    Dashboard for freelancers showing their projects, bids, and earnings.
    """
    template_name = 'users/freelancer_dashboard.html'
    login_url = 'login'
    
    def get(self, request, *args, **kwargs):
        """Check if user is a freelancer before showing dashboard"""
        if request.user.role != 'freelancer':
            return redirect('client-dashboard')
        return super().get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from projects.models import Project, Bid
        
        user = self.request.user
        
        # Get freelancer's active projects
        active_projects = Project.objects.filter(
            freelancer=user,
            status__in=['in_progress']
        ).order_by('-created_at')
        
        # Get freelancer's completed projects
        completed_projects = Project.objects.filter(
            freelancer=user,
            status='completed'
        ).order_by('-created_at')
        
        # Get all bids made by freelancer
        all_bids = Bid.objects.filter(freelancer=user).order_by('-created_at')
        
        # Accepted bids (projects where bid was accepted)
        accepted_bids = all_bids.filter(project__freelancer=user)
        
        # Pending bids (bids waiting for response)
        pending_bids = all_bids.filter(project__freelancer__isnull=True)
        
        # Calculate earnings
        total_earnings = Project.objects.filter(
            freelancer=user,
            status='completed'
        ).aggregate(total=Sum('budget'))['total'] or 0
        
        # Count projects
        total_projects = active_projects.count() + completed_projects.count()
        
        context.update({
            'active_projects': active_projects,
            'completed_projects': completed_projects,
            'total_projects': total_projects,
            'all_bids': all_bids[:10],  # Last 10 bids
            'pending_bids_count': pending_bids.count(),
            'accepted_bids_count': accepted_bids.count(),
            'total_earnings': total_earnings,
            'total_bids': all_bids.count(),
        })
        
        return context


class ClientDashboardView(LoginRequiredMixin, TemplateView):
    """
    Dashboard for clients showing their posted projects, active projects, and spending.
    """
    template_name = 'users/client_dashboard.html'
    login_url = 'login'
    
    def get(self, request, *args, **kwargs):
        """Check if user is a client before showing dashboard"""
        if request.user.role == 'freelancer':
            return redirect('freelancer-dashboard')
        return super().get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from projects.models import Project, Bid
        
        user = self.request.user
        
        # Get all projects posted by client
        all_projects = Project.objects.filter(client=user).order_by('-created_at')
        
        # Open projects (waiting for bids)
        open_projects = all_projects.filter(status='open')
        
        # Active projects (in progress)
        active_projects = all_projects.filter(status='in_progress')
        
        # Completed projects
        completed_projects = all_projects.filter(status='completed')
        
        # Cancelled projects
        cancelled_projects = all_projects.filter(status='cancelled')
        
        # Total bids received for client's projects
        total_bids_received = Bid.objects.filter(
            project__client=user
        ).count()
        
        # Calculate total spending
        total_spending = all_projects.filter(
            status='completed'
        ).aggregate(total=Sum('budget'))['total'] or 0
        
        # Get open projects with bids
        projects_with_bids = []
        for project in open_projects:
            bids_count = project.bids.count()
            projects_with_bids.append({
                'project': project,
                'bids_count': bids_count
            })
        
        context.update({
            'all_projects': all_projects,
            'open_projects': open_projects,
            'active_projects': active_projects,
            'completed_projects': completed_projects,
            'cancelled_projects': cancelled_projects,
            'projects_with_bids': projects_with_bids,
            'total_projects': all_projects.count(),
            'total_spending': total_spending,
            'total_bids_received': total_bids_received,
        })
        
        return context