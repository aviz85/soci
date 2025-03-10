from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import UserPreference, MoodBoard, MoodBoardItem, WellbeingData

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the User model."""
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'bio',
            'profile_image', 'banner_image', 'location', 'website', 'birth_date',
            'private_profile', 'show_online_status', 'last_active', 'account_created',
            'is_verified'
        ]
        read_only_fields = ['id', 'account_created', 'is_verified']
        extra_kwargs = {
            'email': {'write_only': True},
            'birth_date': {'write_only': True}
        }


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name'
        ]
    
    def validate(self, data):
        """Validate that passwords match."""
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Passwords do not match.")
        return data
    
    def create(self, validated_data):
        """Create a new user with encrypted password."""
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class UserPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for the UserPreference model."""
    
    class Meta:
        model = UserPreference
        fields = [
            'id', 'user', 'email_notifications', 'push_notifications',
            'content_language', 'content_sensitivity', 'who_can_message',
            'daily_usage_limit', 'scheduled_downtime_start', 'scheduled_downtime_end'
        ]
        read_only_fields = ['id', 'user']


class MoodBoardItemSerializer(serializers.ModelSerializer):
    """Serializer for the MoodBoardItem model."""
    
    class Meta:
        model = MoodBoardItem
        fields = [
            'id', 'mood_board', 'image', 'text', 'link',
            'position_x', 'position_y', 'created_at'
        ]
        read_only_fields = ['id', 'mood_board', 'created_at']


class MoodBoardSerializer(serializers.ModelSerializer):
    """Serializer for the MoodBoard model."""
    items = MoodBoardItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = MoodBoard
        fields = [
            'id', 'user', 'title', 'description', 'is_current',
            'created_at', 'updated_at', 'items'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class WellbeingDataSerializer(serializers.ModelSerializer):
    """Serializer for the WellbeingData model."""
    
    class Meta:
        model = WellbeingData
        fields = [
            'id', 'user', 'date', 'time_spent', 'sessions_count',
            'interactions_count', 'mood_assessment'
        ]
        read_only_fields = ['id', 'user', 'date'] 