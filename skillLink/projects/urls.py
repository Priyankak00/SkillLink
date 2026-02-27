from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    path('', views.ProjectListView.as_view(), name='project-list'),
    path('marketplace/', views.MarketplaceView.as_view(), name='marketplace'),
    path('new/', views.ProjectCreateView.as_view(), name='project-create'),
    path('my-projects/', views.MyProjectsView.as_view(), name='my-projects'),
    path('<int:pk>/', views.ProjectDetailView.as_view(), name='project-detail'),
    path('<int:pk>/edit/', views.ProjectUpdateView.as_view(), name='project-update'),
    path('<int:pk>/delete/', views.ProjectDeleteView.as_view(), name='project-delete'),
    path('<int:project_pk>/bid/', views.BidCreateFormView.as_view(), name='bid-create'),
    
    path('<int:project_id>/submit-work/', views.SubmitWorkView.as_view(), name='submit-work'),
    path('<int:project_id>/review-work/', views.ReviewWorkView.as_view(), name='review-work'),
    path('<int:project_id>/initiate-payment/', views.InitiatePaymentView.as_view(), name='initiate-payment'),
    path('<int:project_id>/write-review/', views.WriteReviewView.as_view(), name='write-review'),
    
    path('api/create/', views.ProjectCreateAPIView.as_view(), name='api-project-create'),
    path('api/available/', views.AvailableProjectsListView.as_view(), name='api-available-projects'),
    path('api/<int:pk>/', views.ProjectDetailAPIView.as_view(), name='api-project-detail'),
    
    path('api/<int:project_id>/bid/create/', views.BidCreateView.as_view(), name='api-bid-create'),
    path('api/<int:project_id>/bids/', views.BidListView.as_view(), name='api-project-bids'),
    path('api/my-bids/', views.UserBidsListView.as_view(), name='api-my-bids'),
    path('api/bids/<int:pk>/accept/', views.BidAcceptView.as_view(), name='api-bid-accept'),
    path('api/bids/<int:pk>/reject/', views.BidRejectView.as_view(), name='api-bid-reject'),
]