from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.users.models import User


class Connection(models.Model):
    """
    Connections between users (following/followers).
    """
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    followed = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Connection quality metrics
    STRENGTH_CHOICES = [
        ('weak', _('Weak')),
        ('moderate', _('Moderate')),
        ('strong', _('Strong')),
    ]
    strength = models.CharField(
        max_length=10,
        choices=STRENGTH_CHOICES,
        default='weak'
    )
    
    interaction_count = models.PositiveIntegerField(default=0)
    last_interaction = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ('follower', 'followed')
    
    def __str__(self):
        return f"{self.follower.username} follows {self.followed.username}"


class Message(models.Model):
    """
    Private messages between users.
    """
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    body = models.TextField()
    
    # For attachments
    has_attachment = models.BooleanField(default=False)
    
    # Message status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # For voice messages
    is_voice = models.BooleanField(default=False)
    voice_duration = models.PositiveIntegerField(null=True, blank=True)  # in seconds
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Message from {self.sender.username} to {self.recipient.username}"


class MessageAttachment(models.Model):
    """
    Attachments for private messages.
    """
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='message_attachments/')
    
    TYPE_CHOICES = [
        ('image', _('Image')),
        ('video', _('Video')),
        ('audio', _('Audio')),
        ('document', _('Document')),
    ]
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    
    file_name = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField()  # in bytes
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.type} attachment for {self.message}"


class Conversation(models.Model):
    """
    Conversation between users to group messages.
    """
    participants = models.ManyToManyField(User, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # For group conversations
    is_group = models.BooleanField(default=False)
    name = models.CharField(max_length=100, blank=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        if self.is_group and self.name:
            return f"Group: {self.name}"
        
        participants = list(self.participants.all())
        if len(participants) > 3:
            participant_names = ", ".join([user.username for user in participants[:3]])
            return f"Conversation with {participant_names} and others"
        
        participant_names = ", ".join([user.username for user in participants])
        return f"Conversation with {participant_names}"


class ConversationMessage(models.Model):
    """
    Messages within a conversation.
    """
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversation_messages')
    body = models.TextField()
    
    # For attachments
    has_attachment = models.BooleanField(default=False)
    
    # For voice messages
    is_voice = models.BooleanField(default=False)
    voice_duration = models.PositiveIntegerField(null=True, blank=True)  # in seconds
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Message from {self.sender.username} in {self.conversation}"


class ConversationMessageAttachment(models.Model):
    """
    Attachments for conversation messages.
    """
    message = models.ForeignKey(ConversationMessage, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='conversation_attachments/')
    
    TYPE_CHOICES = [
        ('image', _('Image')),
        ('video', _('Video')),
        ('audio', _('Audio')),
        ('document', _('Document')),
    ]
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    
    file_name = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField()  # in bytes
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.type} attachment for message in {self.message.conversation}"


class ConversationRead(models.Model):
    """
    Tracks when users last read a conversation.
    """
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='read_marks')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversation_reads')
    last_read_at = models.DateTimeField()
    
    class Meta:
        unique_together = ('conversation', 'user')
    
    def __str__(self):
        return f"{self.user.username} last read {self.conversation} at {self.last_read_at}"


class Notification(models.Model):
    """
    Notifications for various events.
    """
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    
    TYPE_CHOICES = [
        ('follow', _('New Follower')),
        ('like', _('New Like')),
        ('comment', _('New Comment')),
        ('mention', _('Mention')),
        ('message', _('New Message')),
        ('invitation', _('Invitation')),
        ('system', _('System Notification')),
    ]
    notification_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    
    title = models.CharField(max_length=100)
    message = models.TextField()
    
    # For linking to the relevant object
    link = models.URLField(blank=True)
    
    # Notification status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.notification_type} notification for {self.recipient.username}"


class CollaborativeSpace(models.Model):
    """
    Collaborative spaces for group projects and creative endeavors.
    """
    name = models.CharField(max_length=100)
    description = models.TextField()
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_spaces')
    members = models.ManyToManyField(User, related_name='collaborative_spaces', through='SpaceMembership')
    
    # Space settings
    is_public = models.BooleanField(default=False)
    allows_comments = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name


class SpaceMembership(models.Model):
    """
    Membership in a collaborative space.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    space = models.ForeignKey(CollaborativeSpace, on_delete=models.CASCADE)
    
    ROLE_CHOICES = [
        ('viewer', _('Viewer')),
        ('contributor', _('Contributor')),
        ('editor', _('Editor')),
        ('admin', _('Admin')),
    ]
    role = models.CharField(
        max_length=12,
        choices=ROLE_CHOICES,
        default='contributor'
    )
    
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'space')
    
    def __str__(self):
        return f"{self.user.username} as {self.role} in {self.space.name}" 