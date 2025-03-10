from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Connection, Message, MessageAttachment, Conversation, ConversationMessage,
    ConversationMessageAttachment, ConversationRead, Notification,
    CollaborativeSpace, SpaceMembership
)
from apps.users.serializers import UserSerializer

User = get_user_model()


class ConnectionSerializer(serializers.ModelSerializer):
    """Serializer for the Connection model."""
    follower = UserSerializer(read_only=True)
    followed = UserSerializer(read_only=True)
    followed_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True,
        source='followed'
    )
    
    class Meta:
        model = Connection
        fields = [
            'id', 'follower', 'followed', 'followed_id', 'created_at',
            'strength', 'interaction_count', 'last_interaction'
        ]
        read_only_fields = [
            'id', 'follower', 'created_at', 'interaction_count', 'last_interaction'
        ]


class MessageAttachmentSerializer(serializers.ModelSerializer):
    """Serializer for the MessageAttachment model."""
    
    class Meta:
        model = MessageAttachment
        fields = [
            'id', 'message', 'file', 'type', 'file_name',
            'file_size', 'created_at'
        ]
        read_only_fields = ['id', 'message', 'created_at']


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for the Message model."""
    sender = UserSerializer(read_only=True)
    recipient = UserSerializer(read_only=True)
    recipient_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True,
        source='recipient'
    )
    attachments = MessageAttachmentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Message
        fields = [
            'id', 'sender', 'recipient', 'recipient_id', 'body',
            'has_attachment', 'is_read', 'read_at', 'is_voice',
            'voice_duration', 'created_at', 'attachments'
        ]
        read_only_fields = [
            'id', 'sender', 'has_attachment', 'is_read', 'read_at', 'created_at'
        ]


class ConversationMessageAttachmentSerializer(serializers.ModelSerializer):
    """Serializer for the ConversationMessageAttachment model."""
    
    class Meta:
        model = ConversationMessageAttachment
        fields = [
            'id', 'message', 'file', 'type', 'file_name',
            'file_size', 'created_at'
        ]
        read_only_fields = ['id', 'message', 'created_at']


class ConversationMessageSerializer(serializers.ModelSerializer):
    """Serializer for the ConversationMessage model."""
    sender = UserSerializer(read_only=True)
    attachments = ConversationMessageAttachmentSerializer(many=True, read_only=True)
    
    class Meta:
        model = ConversationMessage
        fields = [
            'id', 'conversation', 'sender', 'body', 'has_attachment',
            'is_voice', 'voice_duration', 'created_at', 'attachments'
        ]
        read_only_fields = [
            'id', 'conversation', 'sender', 'has_attachment', 'created_at'
        ]


class ConversationReadSerializer(serializers.ModelSerializer):
    """Serializer for the ConversationRead model."""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = ConversationRead
        fields = ['id', 'conversation', 'user', 'last_read_at']
        read_only_fields = ['id', 'conversation', 'user']


class ConversationSerializer(serializers.ModelSerializer):
    """Serializer for the Conversation model."""
    participants = UserSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = [
            'id', 'participants', 'created_at', 'updated_at',
            'is_group', 'name', 'last_message', 'unread_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_last_message(self, obj):
        """Get the last message in the conversation."""
        last_message = obj.messages.order_by('-created_at').first()
        if last_message:
            return ConversationMessageSerializer(last_message).data
        return None
    
    def get_unread_count(self, obj):
        """Get the count of unread messages for the current user."""
        user = self.context.get('request').user
        if not user:
            return 0
        
        # Get the last time the user read this conversation
        read_mark = ConversationRead.objects.filter(
            conversation=obj,
            user=user
        ).first()
        
        if not read_mark:
            return obj.messages.exclude(sender=user).count()
        
        # Count messages after the last read time
        return obj.messages.filter(
            created_at__gt=read_mark.last_read_at
        ).exclude(sender=user).count()


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for the Notification model."""
    recipient = UserSerializer(read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'recipient', 'notification_type', 'title',
            'message', 'link', 'is_read', 'read_at', 'created_at'
        ]
        read_only_fields = [
            'id', 'recipient', 'created_at'
        ]


class SpaceMembershipSerializer(serializers.ModelSerializer):
    """Serializer for the SpaceMembership model."""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = SpaceMembership
        fields = ['id', 'user', 'space', 'role', 'joined_at']
        read_only_fields = ['id', 'joined_at']


class CollaborativeSpaceSerializer(serializers.ModelSerializer):
    """Serializer for the CollaborativeSpace model."""
    creator = UserSerializer(read_only=True)
    members = UserSerializer(many=True, read_only=True)
    
    class Meta:
        model = CollaborativeSpace
        fields = [
            'id', 'name', 'description', 'creator', 'members',
            'is_public', 'allows_comments', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'creator', 'created_at', 'updated_at'] 