from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    # API endpoints
    path('api/projects/<int:project_id>/messages/', views.ChatRoomListAPIView.as_view(), name='project-messages'),
    path('api/projects/<int:project_id>/messages/send/', views.SendMessageAPIView.as_view(), name='send-message'),
]