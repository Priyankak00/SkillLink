from rest_framework import permissions

class IsFreelancer(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'freelancer')

class IsNotProjectOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.client != request.user
