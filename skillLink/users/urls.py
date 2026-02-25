from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Profile & CRUD
    path('profile/', views.profile_view, name='profile'),
    path('<int:pk>/', views.user_detail_view, name='user-detail'),  # CRUD: Read, Update, Delete for specific user
    
    # Dashboards
    path('dashboard/', views.DashboardRedirectView.as_view(), name='dashboard'),
    path('dashboard/freelancer/', views.FreelancerDashboardView.as_view(), name='freelancer-dashboard'),
    path('dashboard/client/', views.ClientDashboardView.as_view(), name='client-dashboard'),
]