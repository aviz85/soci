from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from apps.users.models import User


class Tag(models.Model):
    """
    Tags for categorizing content.
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name


class ContentBase(models.Model):
    """
    Base abstract model for all content types.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="%(class)ss")
    tags = models.ManyToManyField(Tag, blank=True, related_name="%(class)ss")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Visibility settings
    VISIBILITY_CHOICES = [
        ('public', _('Public')),
        ('followers', _('Followers')),
        ('private', _('Private')),
    ]
    visibility = models.CharField(
        max_length=10,
        choices=VISIBILITY_CHOICES,
        default='public'
    )
    
    # Content decay
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        abstract = True


class Post(ContentBase):
    """
    User posts which can contain text, images, or other media.
    """
    title = models.CharField(max_length=200, blank=True)
    body = models.TextField()
    
    # Engagement metrics
    view_count = models.PositiveIntegerField(default=0)
    engagement_score = models.FloatField(default=0.0)
    
    def __str__(self):
        if self.title:
            return f"{self.user.username}'s post: {self.title}"
        return f"{self.user.username}'s post: {self.body[:30]}"
    
    def is_expired(self):
        """Check if the post has expired."""
        if self.expires_at and timezone.now() >= self.expires_at:
            return True
        return False
    
    class Meta:
        ordering = ['-created_at']


class Media(models.Model):
    """
    Media items (images, videos, etc.) attached to posts.
    """
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='media')
    
    TYPE_CHOICES = [
        ('image', _('Image')),
        ('video', _('Video')),
        ('audio', _('Audio')),
        ('document', _('Document')),
    ]
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    file = models.FileField(upload_to='post_media/')
    
    # For images/videos
    alt_text = models.CharField(max_length=255, blank=True)
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    
    # For sorting multiple media items
    position = models.PositiveSmallIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.type} for {self.post}"
    
    class Meta:
        ordering = ['position']
        verbose_name_plural = 'media'


class Reaction(models.Model):
    """
    Reactions to content (beyond simple likes).
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reactions')
    
    # Generic relation to support reactions on different content types
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Reaction types
    REACTION_CHOICES = [
        ('like', _('Like')),
        ('love', _('Love')),
        ('laugh', _('Laugh')),
        ('sad', _('Sad')),
        ('angry', _('Angry')),
        ('wow', _('Wow')),
        ('support', _('Support')),
    ]
    reaction_type = models.CharField(max_length=10, choices=REACTION_CHOICES)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'content_type', 'object_id')
    
    def __str__(self):
        return f"{self.user.username} {self.reaction_type}d {self.content_object}"


class Comment(models.Model):
    """
    Comments on content.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    
    # Generic relation to support comments on different content types
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # For nested comments
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies'
    )
    
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # For soft deletion
    is_deleted = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.username}'s comment on {self.content_object}"
    
    class Meta:
        ordering = ['created_at']


class SavedContent(models.Model):
    """
    Content saved by users for later viewing.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_content')
    
    # Generic relation to support saving different content types
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'content_type', 'object_id')
    
    def __str__(self):
        return f"{self.user.username} saved {self.content_object}" 