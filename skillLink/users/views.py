from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.contrib.auth import get_user_model, login, logout
from django.db.models import Sum
import json
from .serializers import RegisterSerializer, UserSerializer, LoginSerializer

User = get_user_model()


@csrf_protect
@require_http_methods(["GET", "POST"])
def register_view(request):
    if request.method == 'GET':
        return render(request, 'users/register.html')
    
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST.dict()
        
        print(f"Registration data received: {data}")
        
        serializer = RegisterSerializer(data=data)
        if not serializer.is_valid():
            print(f"Validation errors: {serializer.errors}")
            return JsonResponse(serializer.errors, status=400)
        
        user = serializer.save()
        login(request, user)
        token, created = Token.objects.get_or_create(user=user)
        
        return JsonResponse({
            'token': token.key,
            'user': {
                'id': user.id,
                'email': user.email,
                'username': user.username,
                'role': getattr(user, 'role', 'client')
            },
            'message': 'Registration successful'
        }, status=201)
    except Exception as e:
        print(f"Registration exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'detail': str(e)}, status=400)


@csrf_protect
@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.method == 'GET':
        return render(request, 'users/login.html')
    
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST.dict()
        
        serializer = LoginSerializer(data=data)
        if not serializer.is_valid():
            return JsonResponse({'detail': serializer.errors}, status=400)
        
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        login(request, user)
        
        return JsonResponse({
            'token': token.key,
            'user': {
                'id': user.id,
                'email': user.email,
                'username': user.username,
                'role': getattr(user, 'role', 'client')
            },
            'message': 'Login successful'
        }, status=200)
    except Exception as e:
        return JsonResponse({'detail': str(e)}, status=400)


@csrf_protect
@require_http_methods(["GET", "POST"])
def logout_view(request):
    try:
        Token.objects.get(user=request.user).delete()
    except Token.DoesNotExist:
        pass
    
    logout(request)
    return redirect('login')


@api_view(['GET', 'PUT', 'PATCH'])
@parser_classes([MultiPartParser, FormParser, JSONParser])
@permission_classes([permissions.IsAuthenticated])
def profile_view(request):
    if request.method == 'GET':
        if request.accepted_renderer.format == 'html' or 'text/html' in request.META.get('HTTP_ACCEPT', ''):
            if not request.user.is_authenticated:
                return redirect('login')
            return render(request, 'users/profile.html', {
                'user': request.user
            })

        if not request.user.is_authenticated:
            return Response(
                {"detail": "Authentication credentials were not provided."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = UserSerializer(request.user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    if not request.user.is_authenticated:
        return Response(
            {"detail": "Authentication credentials were not provided."},
            status=status.HTTP_403_FORBIDDEN
        )

    partial = request.method == 'PATCH'
    serializer = UserSerializer(
        request.user,
        data=request.data,
        partial=partial,
        context={'request': request}
    )
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    serializer.save()
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@parser_classes([MultiPartParser, FormParser, JSONParser])
@permission_classes([permissions.IsAuthenticated])
def user_detail_view(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.user != user and not request.user.is_staff:
        return Response(
            {"detail": "You can only access your own profile."},
            status=status.HTTP_403_FORBIDDEN
        )

    if request.method == 'GET':
        serializer = UserSerializer(user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    if request.method in ['PUT', 'PATCH']:
        partial = request.method == 'PATCH'
        serializer = UserSerializer(
            user,
            data=request.data,
            partial=partial,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    user.delete()
    return Response(
        {"message": "User account deleted successfully"},
        status=status.HTTP_204_NO_CONTENT
    )


class DashboardRedirectView(LoginRequiredMixin, View):
    login_url = 'login'
    
    def get(self, request, *args, **kwargs):
        """Redirect based on user role"""
        if request.user.role == 'freelancer':
            return redirect('freelancer-dashboard')
        else:
            return redirect('client-dashboard')


class FreelancerDashboardView(LoginRequiredMixin, TemplateView):
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
        
        active_projects = Project.objects.filter(
            freelancer=user,
            status__in=['in_progress']
        ).order_by('-created_at')
        
        completed_projects = Project.objects.filter(
            freelancer=user,
            status='completed'
        ).order_by('-created_at')
        
        all_bids = Bid.objects.filter(freelancer=user).order_by('-created_at')
        
        accepted_bids = all_bids.filter(project__freelancer=user)
        
        pending_bids = all_bids.filter(project__freelancer__isnull=True)
        
        total_earnings = Project.objects.filter(
            freelancer=user,
            status='completed'
        ).aggregate(total=Sum('budget'))['total'] or 123000
        
        total_projects = active_projects.count() + completed_projects.count()
        
        context.update({
            'active_projects': active_projects,
            'completed_projects': completed_projects,
            'total_projects': total_projects,
            'all_bids': all_bids[:10],
            'pending_bids_count': pending_bids.count(),
            'accepted_bids_count': accepted_bids.count(),
            'total_earnings': total_earnings,
            'total_bids': all_bids.count(),
        })
        
        return context


class ClientDashboardView(LoginRequiredMixin, TemplateView):
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
        
        all_projects = Project.objects.filter(client=user).order_by('-created_at')
        
        open_projects = all_projects.filter(status='open')
        
        active_projects = all_projects.filter(status='in_progress')
        
        completed_projects = all_projects.filter(status='completed')
        
        cancelled_projects = all_projects.filter(status='cancelled')
        
        total_bids_received = Bid.objects.filter(
            project__client=user
        ).count()
        
        total_spending = all_projects.filter(
            status='completed'
        ).aggregate(total=Sum('budget'))['total'] or 123000
        
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