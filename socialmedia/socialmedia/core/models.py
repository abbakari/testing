from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.validators import FileExtensionValidator
from django.contrib.auth import get_user_model

class User(AbstractUser):
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=30, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    last_seen = models.DateTimeField(auto_now=True)
    profile_picture = models.ImageField(
        upload_to='profile_pics/', 
        null=True, 
        blank=True,
        default='profile_pics/default.png'
    )
    friends = models.ManyToManyField(
        'self', 
        symmetrical=True, 
        blank=True,
        related_name='user_friends'
    )
    
    def __str__(self):
        return self.username

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

class Post(models.Model):
    MEDIA_TYPES = (
        ('text', 'Text'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('audio', 'Audio'),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_posts'
    )
    content = models.TextField()
    media_type = models.CharField(
        max_length=10,
        choices=MEDIA_TYPES,
        default='text'
    )
    media_file = models.FileField(
        upload_to='posts/',
        null=True,
        blank=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'mp4', 'webm', 'ogg', 'mp3', 'wav']
            )
        ]
    )
    image = models.ImageField(
        upload_to='post_images/',
        null=True,
        blank=True
    )
    video = models.FileField(
        upload_to='post_videos/',
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    likes = models.ManyToManyField(
        User,
        related_name='liked_posts',
        blank=True
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Post'
        verbose_name_plural = 'Posts'

    def __str__(self):
        return f"Post by {self.user.username} at {self.created_at}"
    MEDIA_TYPES = (
        ('text', 'Text'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('audio', 'Audio'),
    )
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='user_posts'
    )
    content = models.TextField()
    media_type = models.CharField(
        max_length=10, 
        choices=MEDIA_TYPES, 
        default='text'
    )
    media_file = models.FileField(
        upload_to='posts/',
        null=True,
        blank=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'mp4', 'webm', 'ogg', 'mp3', 'wav']
            )
        ]
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    likes = models.ManyToManyField(
        User, 
        related_name='liked_posts', 
        blank=True
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Post'
        verbose_name_plural = 'Posts'
    
    def __str__(self):
        return f"Post by {self.user.username} at {self.created_at}"

class Comment(models.Model):
    post = models.ForeignKey(
        Post, 
        on_delete=models.CASCADE, 
        related_name='post_comments'
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='user_comments'
    )
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = 'Comment'
        verbose_name_plural = 'Comments'
    
    def __str__(self):
        return f"Comment by {self.user.username} on {self.post}"

class FriendRequest(models.Model):
    from_user = models.ForeignKey(
        User, 
        related_name='sent_requests', 
        on_delete=models.CASCADE
    )
    to_user = models.ForeignKey(
        User, 
        related_name='received_requests', 
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(default=timezone.now)
    accepted = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('from_user', 'to_user')
        verbose_name = 'Friend Request'
        verbose_name_plural = 'Friend Requests'
    
    def __str__(self):
        return f"{self.from_user} to {self.to_user} - {'Accepted' if self.accepted else 'Pending'}"

class Group(models.Model):
    CATEGORY_CHOICES = [
        ('hobbies', 'Hobbies & Interests'),
        ('education', 'Education'),
        ('technology', 'Technology'),
        ('health', 'Health & Wellness'),
        ('business', 'Business'),
        ('entertainment', 'Entertainment'),
    ]
    
    PRIVACY_CHOICES = [
        ('public', 'Public'),
        ('private', 'Private'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    creator = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='created_groups'
    )
    members = models.ManyToManyField(
        User, 
        related_name='joined_groups',
        blank=True
    )
    banner = models.ImageField(
        upload_to='group_banners/', 
        blank=True, 
        null=True
    )
    avatar = models.ImageField(
        upload_to='group_avatars/',
        default='group_avatars/default.png'
    )
    created_at = models.DateTimeField(default=timezone.now)
    category = models.CharField(
        max_length=50, 
        choices=CATEGORY_CHOICES
    )
    privacy = models.CharField(
        max_length=10, 
        choices=PRIVACY_CHOICES, 
        default='public'
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Group'
        verbose_name_plural = 'Groups'
        ordering = ['-created_at']

class GroupPost(models.Model):
    MEDIA_TYPES = (
        ('text', 'Text'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('audio', 'Audio'),
    )
    
    group = models.ForeignKey(
        Group, 
        on_delete=models.CASCADE, 
        related_name='group_posts'
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='user_group_posts'
    )
    content = models.TextField()
    media_file = models.FileField(
        upload_to='group_posts/', 
        blank=True, 
        null=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'mp4', 'webm', 'ogg', 'mp3', 'wav']
            )
        ]
    )
    media_type = models.CharField(
        max_length=10, 
        choices=MEDIA_TYPES, 
        blank=True, 
        null=True
    )
    created_at = models.DateTimeField(default=timezone.now)
    likes = models.ManyToManyField(
        User, 
        related_name='liked_group_posts', 
        blank=True
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Group Post'
        verbose_name_plural = 'Group Posts'

    def __str__(self):
        return f"Post in {self.group.name} by {self.user.username}"

class GroupMessage(models.Model):
    group = models.ForeignKey(
        Group, 
        on_delete=models.CASCADE, 
        related_name='messages'
    )
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    read_by = models.ManyToManyField(
        User, 
        related_name='read_messages', 
        blank=True
    )

    class Meta:
        ordering = ['timestamp']
        verbose_name = 'Group Message'
        verbose_name_plural = 'Group Messages'

    def __str__(self):
        return f"{self.sender.username} in {self.group.name}: {self.content[:20]}..."

class GroupCall(models.Model):
    CALL_TYPE_CHOICES = (
        ('video', 'Video Call'),
        ('audio', 'Audio Call'),
    )
    
    group = models.ForeignKey(
        Group, 
        on_delete=models.CASCADE, 
        related_name='calls'
    )
    creator = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='created_calls'
    )
    call_type = models.CharField(
        max_length=10, 
        choices=CALL_TYPE_CHOICES
    )
    started_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(null=True, blank=True)
    participants = models.ManyToManyField(
        User, 
        related_name='participated_calls', 
        blank=True
    )

    def is_active(self):
        return self.ended_at is None

    class Meta:
        ordering = ['-started_at']
        verbose_name = 'Group Call'
        verbose_name_plural = 'Group Calls'

    def __str__(self):
        status = "Active" if self.is_active() else "Ended"
        return f"{self.get_call_type_display()} in {self.group.name} ({status})"

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('friend_request', 'Friend Request'),
        ('friend_accept', 'Friend Accepted'),
        ('group_invite', 'Group Invitation'),
        ('post_like', 'Post Like'),
        ('post_comment', 'Post Comment'),
        ('message', 'Message'),
        ('call', 'Call'),
    ]
    
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_notifications',
        null=True,
        blank=True
    )
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'

    def __str__(self):
        return f"{self.get_notification_type_display()} for {self.recipient.username}"
    
    
    