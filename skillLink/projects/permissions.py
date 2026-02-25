from rest_framework import permissions

class IsFreelancer(permissions.BasePermission):
    """
    Allows access only to users who have the 'freelancer' role.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'freelancer')

class IsNotProjectOwner(permissions.BasePermission):
    """
    Prevents a client from bidding on their own project.
    """
    def has_object_permission(self, request, view, obj):
        # 'obj' here will be the Project instance
        return obj.client != request.user
