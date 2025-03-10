from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from .models import Tag, Post, Media, Reaction, Comment, SavedContent
from apps.users.serializers import UserSerializer


class TagSerializer(serializers.ModelSerializer):
    """Serializer for the Tag model."""
    
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug', 'created_at']
        read_only_fields = ['id', 'created_at']


class MediaSerializer(serializers.ModelSerializer):
    """Serializer for the Media model."""
    
    class Meta:
        model = Media
        fields = [
            'id', 'post', 'type', 'file', 'alt_text',
            'width', 'height', 'position', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class PostSerializer(serializers.ModelSerializer):
    """Serializer for the Post model."""
    user = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    media = MediaSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        many=True, 
        queryset=Tag.objects.all(),
        write_only=True,
        required=False,
        source='tags'
    )
    is_expired = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Post
        fields = [
            'id', 'user', 'title', 'body', 'visibility', 'expires_at',
            'created_at', 'updated_at', 'tags', 'tag_ids', 'media',
            'view_count', 'engagement_score', 'is_expired'
        ]
        read_only_fields = [
            'id', 'user', 'created_at', 'updated_at',
            'view_count', 'engagement_score'
        ]


class ReactionSerializer(serializers.ModelSerializer):
    """Serializer for the Reaction model."""
    user = UserSerializer(read_only=True)
    content_type_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Reaction
        fields = [
            'id', 'user', 'content_type', 'object_id',
            'reaction_type', 'created_at', 'content_type_name'
        ]
        read_only_fields = ['id', 'user', 'created_at']
    
    def get_content_type_name(self, obj):
        """Get the name of the content type."""
        return obj.content_type.model


class CommentSerializer(serializers.ModelSerializer):
    """Serializer for the Comment model."""
    user = UserSerializer(read_only=True)
    content_type_name = serializers.SerializerMethodField()
    replies_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = [
            'id', 'user', 'content_type', 'object_id', 'parent',
            'body', 'created_at', 'updated_at', 'is_deleted',
            'content_type_name', 'replies_count'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def get_content_type_name(self, obj):
        """Get the name of the content type."""
        return obj.content_type.model
    
    def get_replies_count(self, obj):
        """Get the count of replies to this comment."""
        return obj.replies.count()


class SavedContentSerializer(serializers.ModelSerializer):
    """Serializer for the SavedContent model."""
    user = UserSerializer(read_only=True)
    content_type_name = serializers.SerializerMethodField()
    content_object_repr = serializers.SerializerMethodField()
    
    class Meta:
        model = SavedContent
        fields = [
            'id', 'user', 'content_type', 'object_id',
            'created_at', 'content_type_name', 'content_object_repr'
        ]
        read_only_fields = ['id', 'user', 'created_at']
    
    def get_content_type_name(self, obj):
        """Get the name of the content type."""
        return obj.content_type.model
    
    def get_content_object_repr(self, obj):
        """Get a string representation of the content object."""
        return str(obj.content_object) 