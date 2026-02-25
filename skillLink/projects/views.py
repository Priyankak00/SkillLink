from django.shortcuts import render

# Create your views here.
from rest_framework import generics, permissions
from .models import Project, Bid
from .serializers import ProjectSerializer, BidSerializer

class ProjectListCreateView(generics.ListCreateAPIView):
    queryset = Project.objects.all().order_by('-created_at')
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        # Automatically set the client to the logged-in user
        serializer.save(client=self.request.user)

class BidCreateView(generics.CreateAPIView):
    serializer_class = BidSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # Automatically set the freelancer to the logged-in user
        # Note: You should add logic here to prevent clients from bidding on their own projects!
        serializer.save(freelancer=self.request.user)