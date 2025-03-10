from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Community, CommunityMembership, CommunityRule, 
    CommunityPost, CommunityInvitation, CommunityTopic
)
from apps.users.serializers import UserSerializer
from apps.content.serializers import TagSerializer
from apps.content.models import Tag

User = get_user_model()


class CommunitySerializer(serializers.ModelSerializer):
    """Serializer for the Community model."""
    creator = UserSerializer(read_only=True)
    moderators = UserSerializer(many=True, read_only=True)
    members_count = serializers.IntegerField(read_only=True)
    posts_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Community
        fields = [
            'id', 'name', 'slug', 'description', 'icon', 'banner',
            'creator', 'moderators', 'visibility', 'allow_post_images',
            'allow_post_videos', 'requires_post_approval', 'created_at',
            'updated_at', 'members_count', 'posts_count'
        ]
        read_only_fields = [
            'id', 'creator', 'created_at', 'updated_at',
            'members_count', 'posts_count'
        ]


class CommunityMembershipSerializer(serializers.ModelSerializer):
    """Serializer for the CommunityMembership model."""
    user = UserSerializer(read_only=True)
    community = CommunitySerializer(read_only=True)
    
    class Meta:
        model = CommunityMembership
        fields = [
            'id', 'user', 'community', 'status', 'joined_at',
            'last_active_at', 'muted'
        ]
        read_only_fields = ['id', 'user', 'joined_at']


class CommunityRuleSerializer(serializers.ModelSerializer):
    """Serializer for the CommunityRule model."""
    community = serializers.PrimaryKeyRelatedField(
        queryset=Community.objects.all()
    )
    
    class Meta:
        model = CommunityRule
        fields = [
            'id', 'community', 'title', 'description', 'position',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CommunityPostSerializer(serializers.ModelSerializer):
    """Serializer for the CommunityPost model."""
    user = UserSerializer(read_only=True)
    community = CommunitySerializer(read_only=True)
    community_id = serializers.PrimaryKeyRelatedField(
        queryset=Community.objects.all(),
        write_only=True,
        source='community'
    )
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        many=True, 
        queryset=Tag.objects.all(),
        write_only=True,
        required=False,
        source='tags'
    )
    
    class Meta:
        model = CommunityPost
        fields = [
            'id', 'user', 'community', 'community_id', 'status', 'title',
            'body', 'url', 'is_pinned', 'visibility', 'expires_at',
            'created_at', 'updated_at', 'tags', 'tag_ids',
            'view_count', 'engagement_score'
        ]
        read_only_fields = [
            'id', 'user', 'status', 'created_at', 'updated_at',
            'view_count', 'engagement_score'
        ]


class CommunityInvitationSerializer(serializers.ModelSerializer):
    """Serializer for the CommunityInvitation model."""
    inviter = UserSerializer(read_only=True)
    invitee = UserSerializer(read_only=True)
    community = CommunitySerializer(read_only=True)
    community_id = serializers.PrimaryKeyRelatedField(
        queryset=Community.objects.all(),
        write_only=True,
        source='community'
    )
    invitee_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True,
        source='invitee'
    )
    
    class Meta:
        model = CommunityInvitation
        fields = [
            'id', 'community', 'community_id', 'inviter', 'invitee', 'invitee_id',
            'status', 'message', 'created_at', 'responded_at'
        ]
        read_only_fields = [
            'id', 'inviter', 'status', 'created_at', 'responded_at'
        ]


class CommunityTopicSerializer(serializers.ModelSerializer):
    """Serializer for the CommunityTopic model."""
    community = serializers.PrimaryKeyRelatedField(
        queryset=Community.objects.all()
    )
    created_by = UserSerializer(read_only=True)
    
    class Meta:
        model = CommunityTopic
        fields = [
            'id', 'community', 'name', 'description', 'icon',
            'position', 'created_at', 'created_by'
        ]
        read_only_fields = ['id', 'created_at', 'created_by'] 