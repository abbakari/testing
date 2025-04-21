from django.contrib import admin

# Register your models here.
# core/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Post, Comment, FriendRequest

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('email', 'profile_picture', 'bio', 'location', 'birth_date')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'profile_picture', 'bio'),
        }),
    )

class PostAdmin(admin.ModelAdmin):
    list_display = ('user', 'content', 'media_type', 'created_at')
    list_filter = ('media_type', 'created_at')
    search_fields = ('content', 'user__username')
    raw_id_fields = ('user', 'likes')

class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'created_at')
    search_fields = ('content', 'user__username', 'post__content')
    raw_id_fields = ('user', 'post')

class FriendRequestAdmin(admin.ModelAdmin):
    list_display = ('from_user', 'to_user', 'created_at', 'accepted')
    list_filter = ('accepted', 'created_at')
    search_fields = ('from_user__username', 'to_user__username')
    raw_id_fields = ('from_user', 'to_user')
from django.contrib.sites.models import Site

# # Update the default site
# Site.objects.update_or_create(
#     id=1,  # Default site ID
#     defaults={
#         'domain': 'yourdomain.com',  # Replace with your actual domain
#         'name': 'amaryzooh',    # Replace with your site's display name
#     }
# )

admin.site.register(User, CustomUserAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(FriendRequest, FriendRequestAdmin)