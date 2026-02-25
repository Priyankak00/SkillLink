from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'title', 'category', 'role', 'bio', 'skills', 'profile_picture')
        read_only_fields = ('id', 'username')

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    skills = serializers.ListField(child=serializers.CharField(), required=False, allow_empty=True)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'password', 'title', 'category', 'bio', 'skills', 'role')

    def validate_email(self, value):
        """Ensure email is unique"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already registered.")
        return value

    def create(self, validated_data):
        first_name = validated_data.get('first_name', '')
        last_name = validated_data.get('last_name', '')
        email = validated_data.get('email')
        password = validated_data['password']
        title = validated_data.get('title')
        category = validated_data.get('category')
        bio = validated_data.get('bio')
        skills = validated_data.get('skills', [])
        role = validated_data.get('role', 'client')
        
        # Generate username from email or first_name + last_name
        username = email.split('@')[0] if email else f"{first_name.lower()}.{last_name.lower()}"
        
        # Ensure unique username
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            title=title,
            category=category,
            bio=bio,
            skills=skills,
            role=role
        )
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for login with email and password"""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            raise serializers.ValidationError("Email and password are required.")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid email or password.")

        # Authenticate using username (since Django auth uses username)
        user = authenticate(username=user.username, password=password)
        
        if not user:
            raise serializers.ValidationError("Invalid email or password.")

        data['user'] = user
        return data