from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.users.models import User
from apps.content.models import ContentBase


class Community(models.Model):
    """
    Communities are topic-specific spaces for users to interact.
    """
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField()
    icon = models.ImageField(upload_to='community_icons/', null=True, blank=True)
    banner = models.ImageField(upload_to='community_banners/', null=True, blank=True)
    
    # Creators and moderators
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_communities')
    moderators = models.ManyToManyField(User, related_name='moderated_communities', blank=True)
    
    # Privacy and membership settings
    VISIBILITY_CHOICES = [
        ('public', _('Public')),
        ('restricted', _('Restricted')),
        ('private', _('Private')),
    ]
    visibility = models.CharField(
        max_length=10,
        choices=VISIBILITY_CHOICES,
        default='public',
        help_text=_('Public: visible to all, Restricted: requires membership, Private: invite-only')
    )
    
    # Community settings
    allow_post_images = models.BooleanField(default=True)
    allow_post_videos = models.BooleanField(default=True)
    requires_post_approval = models.BooleanField(default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    members_count = models.PositiveIntegerField(default=0)
    posts_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name_plural = 'communities'
    
    def __str__(self):
        return self.name


class CommunityMembership(models.Model):
    """
    Represents a user's membership in a community.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='community_memberships')
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='memberships')
    
    # Membership status
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('member', _('Member')),
        ('banned', _('Banned')),
    ]
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='member'
    )
    
    # Membership timestamps
    joined_at = models.DateTimeField(auto_now_add=True)
    last_active_at = models.DateTimeField(null=True, blank=True)
    
    # Notification preferences specific to this community
    muted = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('user', 'community')
    
    def __str__(self):
        return f"{self.user.username} in {self.community.name}"


class CommunityRule(models.Model):
    """
    Rules for a community that members must follow.
    """
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='rules')
    title = models.CharField(max_length=100)
    description = models.TextField()
    position = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['position']
    
    def __str__(self):
        return f"{self.community.name} rule: {self.title}"


class CommunityPost(ContentBase):
    """
    Posts specific to a community.
    """
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='posts')
    
    # Post status for moderation
    STATUS_CHOICES = [
        ('pending', _('Pending Approval')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
    ]
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='approved'
    )
    
    title = models.CharField(max_length=200)
    body = models.TextField()
    
    # Optional fields
    url = models.URLField(blank=True)
    
    # Pinned posts
    is_pinned = models.BooleanField(default=False)
    
    # Engagement metrics
    view_count = models.PositiveIntegerField(default=0)
    engagement_score = models.FloatField(default=0.0)
    
    class Meta:
        ordering = ['-is_pinned', '-created_at']
    
    def __str__(self):
        return f"{self.title} in {self.community.name}"


class CommunityInvitation(models.Model):
    """
    Invitations to join a community.
    """
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='invitations')
    inviter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_community_invitations')
    invitee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_community_invitations')
    
    # Invitation status
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('accepted', _('Accepted')),
        ('declined', _('Declined')),
    ]
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ('community', 'inviter', 'invitee')
    
    def __str__(self):
        return f"{self.inviter.username} invited {self.invitee.username} to {self.community.name}"


class CommunityTopic(models.Model):
    """
    Topics within a community for organizing discussions.
    """
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='topics')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)
    position = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_topics')
    
    class Meta:
        ordering = ['position']
        unique_together = ('community', 'name')
    
    def __str__(self):
        return f"{self.name} in {self.community.name}" 