from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Profile Information', {'fields': ('role', 'title', 'category', 'bio', 'skills', 'profile_picture')}),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'title', 'category', 'is_staff')
    list_filter = ('role', 'category', 'is_staff', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'title')


admin.site.register(User, UserAdmin)
