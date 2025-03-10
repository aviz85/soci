from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Custom User model that extends the default Django User model.
    Adds additional fields for the SociSphere platform.
    """
    email = models.EmailField(_('email address'), unique=True)
    bio = models.TextField(blank=True)
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    banner_image = models.ImageField(upload_to='banner_images/', blank=True, null=True)
    location = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    birth_date = models.DateField(null=True, blank=True)
    
    # Privacy settings
    private_profile = models.BooleanField(default=False)
    show_online_status = models.BooleanField(default=True)
    
    # Activity metrics
    last_active = models.DateTimeField(null=True, blank=True)
    account_created = models.DateTimeField(auto_now_add=True)
    
    # Verification
    is_verified = models.BooleanField(default=False)
    
    REQUIRED_FIELDS = ['email']
    
    def __str__(self):
        return self.username
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')


class UserPreference(models.Model):
    """
    User preferences model for storing all user settings.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preferences')
    
    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    
    # Content preferences
    content_language = models.CharField(max_length=10, default='en')
    content_sensitivity = models.CharField(
        max_length=10,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
        ],
        default='medium'
    )
    
    # Privacy preferences
    who_can_message = models.CharField(
        max_length=10,
        choices=[
            ('everyone', 'Everyone'),
            ('followers', 'Followers'),
            ('nobody', 'Nobody'),
        ],
        default='everyone'
    )
    
    # Digital wellbeing
    daily_usage_limit = models.PositiveIntegerField(default=0)  # 0 means no limit (in minutes)
    scheduled_downtime_start = models.TimeField(null=True, blank=True)
    scheduled_downtime_end = models.TimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username}'s preferences"


class MoodBoard(models.Model):
    """
    Mood board for users to express their current interests and emotional state.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mood_boards')
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_current = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s mood board: {self.title}"


class MoodBoardItem(models.Model):
    """
    Individual items on a user's mood board.
    """
    mood_board = models.ForeignKey(MoodBoard, on_delete=models.CASCADE, related_name='items')
    image = models.ImageField(upload_to='mood_board_items/', blank=True, null=True)
    text = models.CharField(max_length=200, blank=True)
    link = models.URLField(blank=True)
    position_x = models.IntegerField(default=0)
    position_y = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Item in {self.mood_board.title}"


class WellbeingData(models.Model):
    """
    Model to track user's digital wellbeing data.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wellbeing_data')
    date = models.DateField(auto_now_add=True)
    time_spent = models.PositiveIntegerField(default=0)  # in seconds
    sessions_count = models.PositiveIntegerField(default=0)
    interactions_count = models.PositiveIntegerField(default=0)
    mood_assessment = models.CharField(
        max_length=10,
        choices=[
            ('positive', 'Positive'),
            ('neutral', 'Neutral'),
            ('negative', 'Negative'),
        ],
        blank=True,
        null=True
    )
    
    class Meta:
        unique_together = ('user', 'date')
    
    def __str__(self):
        return f"{self.user.username}'s wellbeing data on {self.date}" 