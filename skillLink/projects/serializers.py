from rest_framework import serializers
from .models import Project, Bid

class BidSerializer(serializers.ModelSerializer):
    freelancer_name = serializers.ReadOnlyField(source='freelancer.username')

    class Meta:
        model = Bid
        fields = ['id', 'freelancer', 'freelancer_name', 'amount', 'delivery_days', 'proposal', 'created_at']
        read_only_fields = ['freelancer']

class ProjectSerializer(serializers.ModelSerializer):
    client_name = serializers.ReadOnlyField(source='client.username')
    bids = BidSerializer(many=True, read_only=True) # Nested Bids
    bid_count = serializers.IntegerField(source='bids.count', read_only=True)

    class Meta:
        model = Project
        fields = [
            'id', 'title', 'description', 'budget', 'status', 
            'client', 'client_name', 'freelancer', 'bids', 'bid_count', 'created_at'
        ]
        read_only_fields = ['client', 'freelancer', 'status']