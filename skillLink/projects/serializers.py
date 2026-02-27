from rest_framework import serializers
from .models import Project, Bid
from users.models import User


class FreelancerBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class BidSerializer(serializers.ModelSerializer):
    freelancer_name = serializers.ReadOnlyField(source='freelancer.get_full_name')
    freelancer_email = serializers.ReadOnlyField(source='freelancer.email')
    freelancer_details = FreelancerBasicSerializer(source='freelancer', read_only=True)

    class Meta:
        model = Bid
        fields = [
            'id', 'freelancer', 'freelancer_name', 'freelancer_email', 
            'freelancer_details', 'amount', 'delivery_days', 'proposal', 
            'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['freelancer', 'status', 'created_at', 'updated_at']


class ProjectSerializer(serializers.ModelSerializer):
    client_name = serializers.ReadOnlyField(source='client.get_full_name')
    client_details = FreelancerBasicSerializer(source='client', read_only=True)
    freelancer_name = serializers.ReadOnlyField(source='freelancer.get_full_name')
    freelancer_details = FreelancerBasicSerializer(source='freelancer', read_only=True)
    bids = serializers.SerializerMethodField()
    bid_count = serializers.SerializerMethodField()
    user_has_bid = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            'id', 'title', 'description', 'budget', 'status', 
            'client', 'client_name', 'client_details',
            'freelancer', 'freelancer_name', 'freelancer_details',
            'bids', 'bid_count', 'user_has_bid', 'created_at', 'updated_at'
        ]
        read_only_fields = ['client', 'freelancer', 'created_at', 'updated_at']

    def get_bids(self, obj):
        if self.context.get('include_bids'):
            return BidSerializer(obj.bids.all(), many=True).data
        return None

    def get_bid_count(self, obj):
        return obj.bids.count()

    def get_user_has_bid(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.bids.filter(freelancer=request.user).exists()
        return False