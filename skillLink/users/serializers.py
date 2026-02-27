from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    profile_picture_url = serializers.SerializerMethodField()
    profile_picture = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'title', 'category', 'role', 'bio', 'skills',
            'profile_picture', 'profile_picture_url'
        )
        read_only_fields = ('id', 'username')

    def get_profile_picture_url(self, obj):
        request = self.context.get('request')
        if not obj.profile_picture:
            return None
        url = obj.profile_picture.url
        if request:
            return request.build_absolute_uri(url)
        return url
    
    def update(self, instance, validated_data):
        if 'profile_picture' in validated_data:
            instance.profile_picture = validated_data.pop('profile_picture')
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)
    skills = serializers.CharField(required=False, allow_blank=True)  # Accept as string, will parse in validation

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'password', 'confirm_password', 'title', 'category', 'bio', 'skills', 'role')

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already registered.")
        return value
    
    def validate_skills(self, value):
        import json
        if not value:
            return []
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return parsed if isinstance(parsed, list) else []
            except json.JSONDecodeError:
                return []
        return value if isinstance(value, list) else []

    def validate(self, attrs):
        password = attrs.get('password')
        confirm_password = attrs.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})
        
        role = attrs.get('role')
        if not role:
            raise serializers.ValidationError({'role': 'Please select whether you are a Freelancer or Client.'})
        
        if role == 'freelancer':
            category = attrs.get('category')
            if not category or category == '':
                raise serializers.ValidationError({'category': 'Category is required for freelancers.'})
        
        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password', None)
        first_name = validated_data.get('first_name', '')
        last_name = validated_data.get('last_name', '')
        email = validated_data.get('email')
        password = validated_data['password']
        title = validated_data.get('title') or None
        category = validated_data.get('category') or None
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

        user = authenticate(username=user.username, password=password)
        
        if not user:
            raise serializers.ValidationError("Invalid email or password.")

        data['user'] = user
        return data