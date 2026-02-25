from django.urls import path
from . import views

urlpatterns = [
    path('', views.ProjectListCreateView.as_view(), name='project-list-create'),
    path('bid/', views.BidCreateView.as_view(), name='bid-create'),
]